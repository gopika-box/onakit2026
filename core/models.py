from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class Area(models.Model):
    name= models.CharField(max_length=100)

    coordinator = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'coordinator'},
        related_name="coordinator_for_areas"
    )
    def __str__(self):
        return self.name
    
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin','Admin'),
        ('coordinator','Coordinator'),
        ('user','User'),
    )
    role= models.CharField(max_length=20,choices=ROLE_CHOICES)
    person_id = models.CharField(max_length=10,unique=True,null=True,blank=True)
    place = models.CharField(max_length=100,blank=True,null=True)
    area = models.ForeignKey("Area",
                             on_delete=models.SET_NULL,
                             null=True,
                             blank=True)
    def __str__(self):
        return f"{self.username} ({self.role})"
    

    
class Payment(models.Model):
    MONTH_CHOICES = (
        ('Oct','October'),
        ('Nov','November'),
        ('Dec','December'),
        ('Jan','January'),
        ('Feb','February'),
        ('Mar','March'),
        ('Apr','April'),
        ('May','May'),
        ('Jun','June'),
        ('Jul','July'),
    )
    user =  models.ForeignKey(User,on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    month = models.CharField(max_length=10,choices=MONTH_CHOICES)
    year = models.IntegerField(default=2026)
    amount_paid =  models.IntegerField()
    paid_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.month}"
    