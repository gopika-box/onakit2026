from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.contrib.auth.hashers import make_password
from .models import User, Payment, Area



# Create your views here.
def landing_page(request):
    return render(request, "landing.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, "login.html", {"error": "Invalid username or password"})

        login(request, user)
        return redirect("dashboard_redirect")

    return render(request, "login.html")

@login_required
def dashboard_redirect(request):
    role = getattr(request.user, "role", None)

    if request.user.role == "admin":
        return redirect('admin_dashboard')
    elif request.user.role =="coordinator":
        return redirect('coordinator_dashboard')
    else:
        return redirect('user_dashboard')

@login_required
def user_dashboard(request):
    
    MONTHS = ["Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul"]

    payments = Payment.objects.filter(user=request.user)
    payment_dict = {p.month: p for p in payments}
    payment_history =[]
    for m in MONTHS:
        if m in payment_dict:
            payment_history.append({
                "month":m,
                "amount": payment_dict[m].amount_paid,
                "status":"PAID"
            })
        else:
            payment_history.append({
                "month":m,
                "amount": 0,
                "status":"PENDING"
            })

    total_paid = sum(p.amount_paid for p in payments)
    remaining_amount = 3500-total_paid
    progress_percent = round((total_paid / 3500) * 100) if total_paid else 0
    return render(request, "user_dashboard.html",
                  {"payment_history":payment_history,
                   "total_paid":total_paid,
                   "remaining_amount": remaining_amount,
                   "progress_percent":progress_percent})











@login_required
def coordinator_dashboard(request):
    area = request.user.area
    MONTHS = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]

    # Get search query from GET parameters
    search_query = request.GET.get('search', '')

    # Start with all users in the coordinator's area, excluding admins
    users_queryset = User.objects.filter(area=area).exclude(role="admin")

    # If a search query is provided, filter the queryset by first_name
    if search_query:
        users_queryset = users_queryset.filter(first_name__icontains=search_query)

    members = []
    for user in users_queryset: # Loop through the (potentially filtered) users
        payments = Payment.objects.filter(user=user)
        payment_dict = {p.month: p.amount_paid for p in payments}

        row = {
            "user": user,
            "months": [],
            "total_paid": 0
        }
        total = 0
        for m in MONTHS:
            amount = payment_dict.get(m, 0)
            row['months'].append(amount)
            total += amount
        row['total_paid'] = total
        row['balance'] = 3500 - total # Assuming total membership fee is 3500

        members.append(row)

    return render(request, "coordinator_dashboard.html", {
        "members": members,
        "months": MONTHS,
        "area": area,
        "search_query": search_query # Pass the search query back to the template to pre-fill the search box
    })


def logout(request):
    auth_logout(request)
    return redirect("landing_page")



@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect("dashboard_redirect")

    total_members = User.objects.exclude(role="admin").count()
    total_collection = Payment.objects.aggregate(total=Sum("amount_paid"))["total"] or 0

    TARGET = total_members * 3500

    # ✅ ROUND %
    collection_percent = round((total_collection / TARGET) * 100) if TARGET else 0

    area_stats = Area.objects.annotate(
        total_collected=Sum('user__payment__amount_paid')
    ).order_by('name')

    completed_members = 0
    users = User.objects.filter(role="user").annotate(total_paid=Sum('payment__amount_paid'))

    for u in users:
        if (u.total_paid or 0) >= 3500:
            completed_members += 1

    return render(request, "admin_dashboard.html", {
        "total_members": total_members,
        "total_collection": total_collection,
        "completed_members": completed_members,
        "pending_members": total_members - completed_members,
        "area_stats": area_stats,
        "collection_percent": collection_percent
    })

def master_sheet(request):
    # Filter out empty users to prevent DoesNotExist errors
    
    users = User.objects.filter(
        Q(role="user") | Q(role="coordinator")
    ).exclude(person_id__isnull=True).exclude(person_id="")
    
    
    # Improved Search: Matches either Name OR Person ID
    query = request.GET.get('q', '')
    if query:
        users = users.filter(
            Q(first_name__icontains=query) | 
            Q(person_id__icontains=query)
        )
    

    # Pre-calculate totals for the Overview
    total_collection = Payment.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    # Process data for the table
    months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    members_list = []
    for user in users:
        pay_map = {p.month: p.amount_paid for p in user.payment_set.all()}
        total_paid = sum(pay_map.values())
        members_list.append({
            "user": user,
            "pay_map": pay_map,
            "total": total_paid,
            "balance": 3500 - total_paid,
        })

    return render(request, "master_sheet.html", {
        "members": members_list,
        "months": months,
        "total_collection": total_collection,
        "query": query
    })

@login_required
def update_payment(request, user_id, month):
    """Option 3: The Edit Functionality (Database Reflection)"""
    if request.method == "POST":
        amount = request.POST.get("amount") or 0
        target_user = get_object_or_404(User, id=user_id)

        if int(amount) == 0:
            Payment.objects.filter(user=target_user, month=month).delete()
        else:
            # Reflects directly in database
            Payment.objects.update_or_create(
                user=target_user,
                month=month,
                year=2026,
                defaults={"amount_paid": amount, "area": target_user.area}
            )
    return redirect("master_sheet")

from django.contrib.auth.hashers import make_password


def manage_users(request):
    """List and Search Users"""
    query = request.GET.get('q', '')
    users = User.objects.all().order_by('person_id')
    
    if query:
        users = users.filter(
            Q(first_name__icontains=query) | Q(person_id__icontains=query)
        )
    
    return render(request, 'manage_users.html', {'users': users, 'query': query})

# ------------------ ADD USER ------------------
import re
from django.contrib.auth.hashers import make_password

def generate_next_person_id():
    users = User.objects.exclude(person_id__isnull=True).exclude(person_id="")

    max_num = 0
    for u in users:
        match = re.search(r'\d+', u.person_id or "")
        if match:
            num = int(match.group())
            if num > max_num:
                max_num = num

    return f"P{max_num + 1:03d}"


def add_user(request):
    if request.method == "POST":
        fname = request.POST.get('first_name').strip().lower()
        role = request.POST.get('role')
        area_id = request.POST.get('area')
        pwd = request.POST.get('password')

        p_id = generate_next_person_id()

        digits = re.search(r'\d+', p_id).group()
        last_two = digits[-2:]

        base_username = f"{fname}{last_two}"
        username = base_username

        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        User.objects.create(
            username=username,
            person_id=p_id,
            first_name=fname,
            role=role,
            area_id=area_id,
            password=make_password(pwd)
        )

        # 🔥 PASS DATA TO TEMPLATE FOR POPUP
        areas = Area.objects.all()
        return render(request, 'user_form.html', {
            'areas': areas,
            'next_id': generate_next_person_id(),
            'edit_user': None,
            'created_username': username,
            'created_password': pwd
        })

    areas = Area.objects.all()
    return render(request, 'user_form.html', {
        'areas': areas,
        'next_id': generate_next_person_id(),
        'edit_user': None
    })

def edit_user(request, user_id):
    """Update Existing User Details"""
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        user_to_edit.first_name = request.POST.get('first_name')
        user_to_edit.person_id = request.POST.get('person_id')
        user_to_edit.role = request.POST.get('role')
        user_to_edit.area_id = request.POST.get('area')
        
        # Only update password if a new one is provided
        new_pwd = request.POST.get('password')
        if new_pwd:
            user_to_edit.password = make_password(new_pwd)
            
        user_to_edit.save()
        return redirect('manage_users')
    
    areas = Area.objects.all()
    return render(request, 'user_form.html', {'edit_user': user_to_edit, 'areas': areas, 'title': 'Edit User'})

def delete_user(request, user_id):
    """Deletes a user and their associated data."""
    user_to_delete = get_object_or_404(User, id=user_id)
    
    # Safety: Prevent the admin from deleting themselves
    if user_to_delete == request.user:
        # You can add a message here later
        return redirect('manage_users')
        
    user_to_delete.delete()
    return redirect('manage_users')