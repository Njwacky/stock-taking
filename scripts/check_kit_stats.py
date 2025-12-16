import os, sys, json
# Ensure repo root is on path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
import django
django.setup()

from django.db.models import Sum, Count, F
from stockT.models import Kit

qs = Kit.objects.values('kit_type_fk__name').annotate(
    kit_type=F('kit_type_fk__name'),
    total_quantity=Sum('quantity'),
    user_count=Count('user', distinct=True)
).order_by('-total_quantity')

data = list(qs)
print('KIT_STATS_LEN=', len(data))
print(json.dumps(data, ensure_ascii=False, indent=2))
