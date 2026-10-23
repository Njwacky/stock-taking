"""Private, general-purpose inventories; never query legacy kit data here."""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect, render

from .models import Inventory, InventoryProduct


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class ProductForm(forms.ModelForm):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['version'].initial = self.instance.version

    class Meta:
        model = InventoryProduct
        fields = ['name', 'sku', 'quantity', 'unit', 'location', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def clean_sku(self):
        sku = self.cleaned_data['sku']
        duplicates = InventoryProduct.objects.filter(inventory=self.instance.inventory, sku=sku)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('This product code already exists in this workspace.')
        return sku


@login_required
@require_http_methods(['GET', 'POST'])
def workspace_list(request):
    form = InventoryForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        inventory = form.save(commit=False)
        inventory.owner = request.user
        inventory.save()
        messages.success(request, 'Workspace created. Add your first product below.')
        return redirect('workspace_detail', workspace_id=inventory.pk)
    return render(request, 'workspaces/list.html', {
        'form': form, 'workspaces': Inventory.objects.filter(owner=request.user),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def workspace_detail(request, workspace_id, product_id=None):
    inventory = get_object_or_404(Inventory, pk=workspace_id, owner=request.user)
    product = (get_object_or_404(InventoryProduct, pk=product_id, inventory=inventory)
               if product_id is not None else InventoryProduct(inventory=inventory))
    form = ProductForm(request.POST if request.method == 'POST' else None, instance=product)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                if product_id is not None:
                    # Compare-and-swap prevents a stale browser tab overwriting newer stock.
                    fields = ProductForm.Meta.fields
                    updated = InventoryProduct.objects.filter(
                        pk=product.pk, inventory=inventory,
                        version=form.cleaned_data['version'],
                    ).update(**{field: form.cleaned_data[field] for field in fields},
                             version=form.cleaned_data['version'] + 1)
                    if not updated:
                        form.add_error(None, 'This product changed since you opened it. Reload the page before editing again.')
                else:
                    form.save()
        except IntegrityError:
            # The database constraint also protects simultaneous duplicate submissions.
            form.add_error('sku', 'This product code already exists in this workspace.')
        if not form.errors:
            messages.success(request, 'Product saved in this workspace.')
            return redirect('workspace_detail', workspace_id=inventory.pk)
    products = Paginator(inventory.products.all(), 50).get_page(request.GET.get('page'))
    return render(request, 'workspaces/detail.html', {
        'workspace': inventory, 'products': products, 'product_count': products.paginator.count,
        'form': form, 'editing': product_id is not None,
    })
