from decimal import Decimal
from django.db import models


class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('materials', 'Materials'),
        ('packaging', 'Packaging'),
        ('shipping', 'Shipping'),
        ('marketing', 'Marketing'),
        ('salary', 'Salary'),
        ('rent', 'Rent'),
        ('other', 'Other'),
    )
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField()
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} (₹{self.amount})'
