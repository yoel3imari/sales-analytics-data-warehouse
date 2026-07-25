"""Product catalog generator for synthetic sales data.

Generates 80 products across 6 categories (Electronics, Clothing,
Home & Garden, Books, Sports, Food & Beverage) with realistic
attribute distributions.
"""

from datetime import date, timedelta

import numpy as np
from faker import Faker

COLORS = [
    "Black", "White", "Red", "Blue", "Green", "Silver", "Gold",
    "Gray", "Navy", "Beige", "Brown", "Pink", "Purple", "Orange",
    "Yellow", "Teal", "Maroon", "Charcoal", "Ivory", "Mint",
]

SIZES_STANDARD = ["S", "M", "L", "XL"]
SIZE_NA = "N/A"

# Each tuple: (name, category, subcategory, brand, min_price, max_price, min_weight, max_weight, has_size)
PRODUCT_DEFS: list[tuple[str, str, str, str, float, float, float, float, bool]] = [
    # ── Electronics – Smartphones (5) ──
    ("TechPro Smartphone X1", "Electronics", "Smartphones", "TechPro", 699, 1299, 0.15, 0.25, False),
    ("MegaGadget Galaxy S24", "Electronics", "Smartphones", "MegaGadget", 599, 1199, 0.16, 0.24, False),
    ("ElectroWave Bolt Pro", "Electronics", "Smartphones", "ElectroWave", 499, 999, 0.14, 0.22, False),
    ("DigiLife Pixel 9", "Electronics", "Smartphones", "DigiLife", 649, 1099, 0.17, 0.26, False),
    ("TechPro Nova Lite", "Electronics", "Smartphones", "TechPro", 299, 599, 0.13, 0.20, False),
    # ── Electronics – Laptops (5) ──
    ("TechPro Book Pro 16", "Electronics", "Laptops", "TechPro", 1199, 2499, 1.20, 2.20, False),
    ("MegaGadget UltraBook Air", "Electronics", "Laptops", "MegaGadget", 899, 1799, 0.90, 1.50, False),
    ("ElectroWave Spin 15", "Electronics", "Laptops", "ElectroWave", 699, 1499, 1.50, 2.50, False),
    ("DigiLife ThinkPad X1", "Electronics", "Laptops", "DigiLife", 1299, 2199, 1.10, 1.80, False),
    ("TechPro Gaming Rig 17", "Electronics", "Laptops", "TechPro", 1499, 2999, 2.00, 3.50, False),
    # ── Electronics – Headphones (3) ──
    ("ElectroWave AirPods Pro", "Electronics", "Headphones", "ElectroWave", 199, 349, 0.04, 0.08, False),
    ("MegaGadget Studio Buds", "Electronics", "Headphones", "MegaGadget", 99, 279, 0.03, 0.07, False),
    ("DigiLife Noise Cancelling 9000", "Electronics", "Headphones", "DigiLife", 249, 449, 0.20, 0.35, False),
    # ── Electronics – Tablets (3) ──
    ("TechPro Tab S9", "Electronics", "Tablets", "TechPro", 499, 899, 0.40, 0.70, False),
    ("MegaGadget iPad Air", "Electronics", "Tablets", "MegaGadget", 599, 1099, 0.45, 0.68, False),
    ("ElectroWave Surface Pro 10", "Electronics", "Tablets", "ElectroWave", 799, 1599, 0.60, 1.00, False),
    # ── Electronics – Accessories (4) ──
    ("DigiLife Wireless Charger", "Electronics", "Accessories", "DigiLife", 19, 59, 0.05, 0.15, False),
    ("TechPro USB-C Hub", "Electronics", "Accessories", "TechPro", 29, 79, 0.03, 0.10, False),
    ("MegaGadget Bluetooth Speaker", "Electronics", "Accessories", "MegaGadget", 39, 149, 0.20, 0.80, False),
    ("TechPro Power Bank 20000", "Electronics", "Accessories", "TechPro", 29, 89, 0.15, 0.50, False),
    # ── Clothing – T-Shirts (4) ──
    ("StyleCo Classic Tee", "Clothing", "T-Shirts", "StyleCo", 19, 49, 0.10, 0.20, True),
    ("UrbanFit Graphic Tee", "Clothing", "T-Shirts", "UrbanFit", 24, 55, 0.10, 0.20, True),
    ("ComfortWear Premium Tee", "Clothing", "T-Shirts", "ComfortWear", 29, 69, 0.12, 0.22, True),
    ("StyleCo Athletic Tee", "Clothing", "T-Shirts", "StyleCo", 22, 45, 0.10, 0.18, True),
    # ── Clothing – Jeans (3) ──
    ("UrbanFit Slim Jeans", "Clothing", "Jeans", "UrbanFit", 49, 89, 0.40, 0.70, True),
    ("ComfortWear Relaxed Fit Jeans", "Clothing", "Jeans", "ComfortWear", 45, 85, 0.42, 0.72, True),
    ("StyleCo Bootcut Jeans", "Clothing", "Jeans", "StyleCo", 39, 79, 0.40, 0.68, True),
    # ── Clothing – Jackets (3) ──
    ("UrbanFit Leather Jacket", "Clothing", "Jackets", "UrbanFit", 89, 199, 0.60, 1.20, True),
    ("ComfortWear Puffer Jacket", "Clothing", "Jackets", "ComfortWear", 69, 149, 0.40, 0.90, True),
    ("StyleCo Denim Jacket", "Clothing", "Jackets", "StyleCo", 59, 129, 0.50, 1.00, True),
    # ── Clothing – Shoes (3) ──
    ("ActiveLife Running Shoes", "Clothing", "Shoes", "ActiveLife", 59, 149, 0.30, 0.50, True),
    ("UrbanFit Casual Sneakers", "Clothing", "Shoes", "UrbanFit", 49, 119, 0.30, 0.50, True),
    ("ComfortWear Hiking Boots", "Clothing", "Shoes", "ComfortWear", 79, 179, 0.50, 0.90, True),
    # ── Clothing – Accessories (2) ──
    ("StyleCo Leather Belt", "Clothing", "Accessories", "StyleCo", 29, 69, 0.08, 0.15, True),
    ("UrbanFit Baseball Cap", "Clothing", "Accessories", "UrbanFit", 15, 35, 0.05, 0.10, True),
    # ── Home & Garden – Furniture (5) ──
    ("HomeElegance Sofa Set", "Home & Garden", "Furniture", "HomeElegance", 499, 1999, 15.0, 40.0, False),
    ("CozyLiving Coffee Table", "Home & Garden", "Furniture", "CozyLiving", 129, 499, 8.0, 20.0, False),
    ("HomeElegance Bookshelf", "Home & Garden", "Furniture", "HomeElegance", 89, 349, 10.0, 25.0, False),
    ("GardenPlus Patio Set", "Home & Garden", "Furniture", "GardenPlus", 299, 899, 12.0, 30.0, False),
    ("CozyLiving Bed Frame", "Home & Garden", "Furniture", "CozyLiving", 249, 799, 15.0, 35.0, False),
    # ── Home & Garden – Kitchen (4) ──
    ("HomeElegance Chef Knife Set", "Home & Garden", "Kitchen", "HomeElegance", 49, 149, 0.50, 1.20, False),
    ("CozyLiving Cookware Set", "Home & Garden", "Kitchen", "CozyLiving", 79, 249, 2.00, 5.00, False),
    ("HomeElegance Blender Pro", "Home & Garden", "Kitchen", "HomeElegance", 39, 129, 1.50, 3.50, False),
    ("GardenPlus Herb Garden Kit", "Home & Garden", "Kitchen", "GardenPlus", 19, 49, 0.30, 0.80, False),
    # ── Home & Garden – Garden (3) ──
    ("GardenPlus Garden Tool Set", "Home & Garden", "Garden", "GardenPlus", 29, 89, 1.00, 3.00, False),
    ("HomeElegance Outdoor Planter", "Home & Garden", "Garden", "HomeElegance", 19, 69, 0.50, 2.00, False),
    ("GardenPlus Watering System", "Home & Garden", "Garden", "GardenPlus", 34, 79, 0.40, 1.50, False),
    # ── Home & Garden – Decor (3) ──
    ("CozyLiving Table Lamp", "Home & Garden", "Decor", "CozyLiving", 29, 89, 0.30, 0.80, False),
    ("HomeElegance Wall Art Set", "Home & Garden", "Decor", "HomeElegance", 39, 149, 0.50, 2.00, False),
    ("CozyLiving Throw Pillow Set", "Home & Garden", "Decor", "CozyLiving", 19, 59, 0.20, 0.60, False),
    # ── Books – Fiction (3) ──
    ("The Silent Echo", "Books", "Fiction", "PageTurner Press", 14, 28, 0.20, 0.50, False),
    ("Midnight Chronicles", "Books", "Fiction", "PageTurner Press", 12, 26, 0.20, 0.50, False),
    ("Ocean of Stars", "Books", "Fiction", "PageTurner Press", 15, 30, 0.25, 0.55, False),
    # ── Books – Non-Fiction (3) ──
    ("The Innovation Mindset", "Books", "Non-Fiction", "KnowledgeFirst", 18, 35, 0.25, 0.50, False),
    ("World History Unlocked", "Books", "Non-Fiction", "WorldView Books", 22, 40, 0.30, 0.60, False),
    ("The Science of Habit", "Books", "Non-Fiction", "KnowledgeFirst", 16, 32, 0.20, 0.45, False),
    # ── Books – Science (2) ──
    ("Quantum Physics Simplified", "Books", "Science", "KnowledgeFirst", 24, 45, 0.25, 0.50, False),
    ("Evolution: A New Perspective", "Books", "Science", "WorldView Books", 20, 38, 0.25, 0.55, False),
    # ── Books – History (2) ──
    ("Ancient Civilizations", "Books", "History", "WorldView Books", 18, 34, 0.25, 0.55, False),
    ("The Roaring Twenties", "Books", "History", "KnowledgeFirst", 16, 30, 0.20, 0.50, False),
    # ── Sports – Fitness (3) ──
    ("ActiveLife Yoga Mat", "Sports", "Fitness", "ActiveLife", 19, 59, 0.50, 1.50, False),
    ("PeakPerformance Resistance Bands", "Sports", "Fitness", "PeakPerformance", 14, 39, 0.10, 0.30, False),
    ("SportMax Adjustable Dumbbells", "Sports", "Fitness", "SportMax", 49, 199, 5.00, 15.00, False),
    # ── Sports – Outdoor (3) ──
    ("SportMax Camping Tent", "Sports", "Outdoor", "SportMax", 79, 299, 3.00, 8.00, False),
    ("ActiveLife Hiking Backpack", "Sports", "Outdoor", "ActiveLife", 49, 149, 0.50, 1.50, False),
    ("PeakPerformance Insulated Cooler", "Sports", "Outdoor", "PeakPerformance", 29, 89, 1.00, 3.00, False),
    # ── Sports – Team Sports (2) ──
    ("SportMax Soccer Ball", "Sports", "Team Sports", "SportMax", 19, 59, 0.30, 0.50, False),
    ("ActiveLife Basketball", "Sports", "Team Sports", "ActiveLife", 24, 69, 0.35, 0.60, False),
    # ── Sports – Water Sports (2) ──
    ("PeakPerformance Swim Goggles", "Sports", "Water Sports", "PeakPerformance", 12, 34, 0.02, 0.08, False),
    ("SportMax Inflatable Kayak", "Sports", "Water Sports", "SportMax", 149, 399, 5.00, 12.00, False),
    # ── Food & Beverage – Snacks (3) ──
    ("FreshBite Premium Trail Mix", "Food & Beverage", "Snacks", "FreshBite", 5, 14, 0.10, 0.40, False),
    ("Nature's Best Organic Granola", "Food & Beverage", "Snacks", "Nature's Best", 6, 15, 0.20, 0.50, False),
    ("FreshBite Protein Bars Variety", "Food & Beverage", "Snacks", "FreshBite", 8, 18, 0.15, 0.35, False),
    # ── Food & Beverage – Beverages (3) ──
    ("Nature's Best Organic Coffee", "Food & Beverage", "Beverages", "Nature's Best", 10, 28, 0.15, 0.40, False),
    ("GourmetDelight Herbal Tea Collection", "Food & Beverage", "Beverages", "GourmetDelight", 8, 22, 0.10, 0.30, False),
    ("FreshBite Cold Brew Concentrate", "Food & Beverage", "Beverages", "FreshBite", 9, 19, 0.20, 0.50, False),
    # ── Food & Beverage – Gourmet (2) ──
    ("GourmetDelight Extra Virgin Olive Oil", "Food & Beverage", "Gourmet", "GourmetDelight", 12, 34, 0.30, 0.80, False),
    ("GourmetDelight Artisan Chocolate Box", "Food & Beverage", "Gourmet", "GourmetDelight", 15, 45, 0.15, 0.40, False),
    # ── Food & Beverage – Organic (2) ──
    ("Nature's Best Organic Honey", "Food & Beverage", "Organic", "Nature's Best", 8, 22, 0.15, 0.45, False),
    ("FreshBite Organic Dried Fruit Mix", "Food & Beverage", "Organic", "FreshBite", 6, 16, 0.10, 0.35, False),
]


def generate_products(
    rng: np.random.Generator,
    *,
    num: int = 80,
) -> list[dict]:
    """Generate a catalog of products with realistic attributes.

    Args:
        rng: Seeded NumPy random generator for reproducibility.
        num: Number of products to generate (must match PRODUCT_DEFS length).

    Returns:
        List of product dicts matching the PRODUCT_COLUMNS schema
        from src.config.
    """
    fake = Faker()
    Faker.seed(int(rng.integers(0, 2**31)))

    ref_end = date(2025, 12, 31)
    ref_start = date(2023, 1, 1)
    ref_ord_start = ref_start.toordinal()
    ref_ord_end = ref_end.toordinal()

    products: list[dict] = []
    for i, (name, cat, sub, brand, pmin, pmax, wmin, wmax, has_size) in enumerate(PRODUCT_DEFS[:num], start=1):
        list_price = round(rng.uniform(pmin, pmax), 2)
        cost_ratio = rng.uniform(0.40, 0.70)
        standard_cost = round(list_price * cost_ratio, 2)

        color = rng.choice(COLORS)
        size = rng.choice(SIZES_STANDARD) if has_size else SIZE_NA
        weight_kg = round(rng.uniform(wmin, wmax), 2)

        launch_ord = int(rng.integers(ref_ord_start, ref_ord_end + 1))
        launch_date = date.fromordinal(launch_ord)

        # 10 % of products are discontinued
        discontinued_date: date | None = None
        if rng.random() < 0.10:
            discont_ord = int(rng.integers(launch_ord, ref_ord_end + 1))
            discontinued_date = date.fromordinal(discont_ord)

        products.append({
            "product_id": f"PROD-{i:05d}",
            "product_name": name,
            "category": cat,
            "subcategory": sub,
            "brand": brand,
            "list_price": list_price,
            "standard_cost": standard_cost,
            "color": color,
            "size": size,
            "weight_kg": weight_kg,
            "launch_date": launch_date.isoformat(),
            "discontinued_date": discontinued_date.isoformat() if discontinued_date else None,
        })

    return products
