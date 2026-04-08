import pandas as pd
from core.models import User, Area, Payment

MONTHS = ["Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul"]

def run():

    file = "onakit_data.xlsx"

    df = pd.read_excel(file, sheet_name="Master Sheet", header=1)

    for _, row in df.iterrows():

        person_id = str(row["Person ID"]).strip()
        name = str(row["Name"]).strip()
        area_name = str(row["Area"]).strip()

        if person_id == "nan":
            continue

        area, _ = Area.objects.get_or_create(name=area_name)

        user, _ = User.objects.get_or_create(
            username=person_id,
            defaults={
                "person_id": person_id,
                "first_name": name,
                "role": "user",
                "area": area
            }
        )

        for month in MONTHS:

            amount = row.get(month)

            # skip empty cells
            if pd.isna(amount):
                continue

            try:
                amount = float(amount)
            except:
                # skip values like 't', 'paid', etc
                continue

            if amount <= 0:
                continue

            Payment.objects.get_or_create(
                user=user,
                area=area,
                month=month,
                defaults={
                    "amount_paid": int(amount)
                }
            )

    print("✅ Excel data imported successfully!")