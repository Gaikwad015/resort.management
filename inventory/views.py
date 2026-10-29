from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import InventoryCategory, Supplier, InventoryItem, StockTransaction, PurchaseOrder, PurchaseOrderItem, WastageRecord
from .serializers import (
    InventoryCategorySerializer, SupplierSerializer, InventoryItemSerializer,
    StockTransactionSerializer, PurchaseOrderSerializer, WastageRecordSerializer
)

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related('category', 'preferred_supplier').all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock_alerts(self, request):
        """Returns items where current stock is at or below minimum threshold."""
        low_stock_items = [item for item in self.get_queryset() if item.is_low_stock]
        return Response({
            'count': len(low_stock_items),
            'items': InventoryItemSerializer(low_stock_items, many=True).data
        })

    @action(detail=True, methods=['post'], url_path='adjust-stock')
    @transaction.atomic
    def adjust_stock(self, request, pk=None):
        """
        Records a stock movement (USAGE_OUT, PURCHASE_IN, WASTAGE_OUT, RESTAURANT_OUT).
        Enforces database locking and strictly prevents negative stock.
        """
        item = InventoryItem.objects.select_for_update().get(pk=pk)
        qty = Decimal(str(request.data.get('quantity', '0.00')))
        tx_type = request.data.get('transaction_type', 'USAGE_OUT')
        ref = request.data.get('reference', 'Direct Adjustment')
        cost = Decimal(str(request.data.get('unit_cost', item.unit_cost)))

        try:
            item.record_stock_movement(
                qty=qty,
                tx_type=tx_type,
                user=request.user,
                reference=ref,
                cost=cost
            )
            return Response({
                'message': f'Stock updated for {item.name}. New balance: {item.current_stock} {item.unit}.',
                'item': InventoryItemSerializer(item).data
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('supplier', 'created_by', 'approved_by').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_po(self, request, pk=None):
        po = self.get_object()
        po.status = PurchaseOrder.Status.APPROVED
        po.approved_by = request.user
        po.save()
        return Response({'message': f'Purchase Order #{po.po_number} approved.', 'status': po.status})

    @action(detail=True, methods=['post'], url_path='receive-goods')
    @transaction.atomic
    def receive_goods(self, request, pk=None):
        """
        Receives goods against an approved PO and automatically increments inventory stock.
        """
        po = self.get_object()
        if po.status != PurchaseOrder.Status.APPROVED:
            return Response({'error': 'Can only receive goods for an APPROVED Purchase Order.'}, status=status.HTTP_400_BAD_REQUEST)

        for line in po.items.all():
            item = InventoryItem.objects.select_for_update().get(id=line.item.id)
            item.record_stock_movement(
                qty=line.quantity_ordered,
                tx_type='PURCHASE_IN',
                user=request.user,
                reference=f"PO #{po.po_number}",
                cost=line.unit_cost
            )
            line.quantity_received = line.quantity_ordered
            line.save()

        po.status = PurchaseOrder.Status.RECEIVED
        po.received_at = timezone.now()
        po.save()

        return Response({
            'message': f'Goods for PO #{po.po_number} successfully received. Inventory stock updated.',
            'status': po.status
        })


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]


class WastageViewSet(viewsets.ModelViewSet):
    queryset = WastageRecord.objects.select_related('item', 'recorded_by').all()
    serializer_class = WastageRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        wastage = serializer.save(recorded_by=self.request.user)
        # Deduct from stock
        item = InventoryItem.objects.select_for_update().get(id=wastage.item.id)
        item.record_stock_movement(
            qty=wastage.quantity,
            tx_type='WASTAGE_OUT',
            user=self.request.user,
            reference=f"Wastage: {wastage.reason}"
        )
