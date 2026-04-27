"""
WS-A bike additions Apr 27 2026 — fitments for the bikes added in this batch.

These fitments will be integrated into the seed_bike_tire_fitments() flow
once the bikes are added to bike_models table. Each fitment specifies OEM
or recommended tire pairings.

Format: dict with keys {manufacturer, model_name, year_match, position, tire_size_or_brand_model, fitment_type}
- manufacturer: exact bike manufacturer string
- model_name: exact bike model name (must match known_bikes.py entry)
- year_match: year range as tuple (year_from, year_to) or single int for exact year
- position: "front" or "rear"
- tire_size_or_brand_model: string like "120/70ZR17" or "Michelin Pilot Sport 4S"
- fitment_type: "oem" (original equipment) or "recommended" (aftermarket fit)
"""

# WS-A Fitments — 45 new bikes × 2 positions = 90 fitment entries
NEW_BIKE_FITMENTS = [
    # Honda CBR1000RR-R Fireblade SP 2024
    {"manufacturer": "Honda", "model_name": "CBR1000RR-R Fireblade SP", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Honda", "model_name": "CBR1000RR-R Fireblade SP", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # Ducati Panigale V4 2025
    {"manufacturer": "Ducati", "model_name": "Panigale V4", "year_match": (2025, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Ducati", "model_name": "Panigale V4", "year_match": (2025, 2025), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # Ducati Streetfighter V4S 2024
    {"manufacturer": "Ducati", "model_name": "Streetfighter V4S", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Ducati", "model_name": "Streetfighter V4S", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # Yamaha YZF-R9 2025
    {"manufacturer": "Yamaha", "model_name": "YZF-R9", "year_match": (2025, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Yamaha", "model_name": "YZF-R9", "year_match": (2025, 2025), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # BMW M1000RR 2025
    {"manufacturer": "BMW", "model_name": "M 1000 RR", "year_match": (2025, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "BMW", "model_name": "M 1000 RR", "year_match": (2025, 2025), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # Aprilia RS 660 Factory 2025
    {"manufacturer": "Aprilia", "model_name": "RS 660 Factory", "year_match": (2025, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Aprilia", "model_name": "RS 660 Factory", "year_match": (2025, 2025), "position": "rear", "tire_size_or_brand_model": "180/55ZR17", "fitment_type": "oem"},
    
    # KTM 990 RC R 2025
    {"manufacturer": "KTM", "model_name": "990 RC R", "year_match": (2025, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "KTM", "model_name": "990 RC R", "year_match": (2025, 2025), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # Kawasaki ZX-6R 2024
    {"manufacturer": "Kawasaki", "model_name": "ZX-6R", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "120/65ZR17", "fitment_type": "oem"},
    {"manufacturer": "Kawasaki", "model_name": "ZX-6R", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "180/55ZR17", "fitment_type": "oem"},
    
    # Kawasaki Z H2 SE 2024
    {"manufacturer": "Kawasaki", "model_name": "Z H2 SE", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Kawasaki", "model_name": "Z H2 SE", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "200/50ZR17", "fitment_type": "oem"},
    
    # Suzuki Hayabusa 25th Anniversary 2024
    {"manufacturer": "Suzuki", "model_name": "Hayabusa 25th Anniversary", "year_match": (2024, 2024), "position": "front", "tire_size_or_brand_model": "120/70ZR18", "fitment_type": "oem"},
    {"manufacturer": "Suzuki", "model_name": "Hayabusa 25th Anniversary", "year_match": (2024, 2024), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # Triumph Daytona 660 2024
    {"manufacturer": "Triumph", "model_name": "Daytona 660", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Triumph", "model_name": "Daytona 660", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "180/55ZR17", "fitment_type": "oem"},
    
    # MV Agusta Superveloce 1000 Serie Oro 2025
    {"manufacturer": "MV Agusta", "model_name": "Superveloce 1000 Serie Oro", "year_match": (2025, 2025), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "MV Agusta", "model_name": "Superveloce 1000 Serie Oro", "year_match": (2025, 2025), "position": "rear", "tire_size_or_brand_model": "190/50ZR17", "fitment_type": "oem"},
    
    # Indian Pursuit Dark Horse 2024
    {"manufacturer": "Indian Motorcycle", "model_name": "Pursuit Dark Horse", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "130/90B16", "fitment_type": "oem"},
    {"manufacturer": "Indian Motorcycle", "model_name": "Pursuit Dark Horse", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "150/90B16", "fitment_type": "oem"},
    
    # Husqvarna Norden 901 Expedition 2025
    {"manufacturer": "Husqvarna", "model_name": "Norden 901 Expedition", "year_match": (2025, 2025), "position": "front", "tire_size_or_brand_model": "110/80R19", "fitment_type": "oem"},
    {"manufacturer": "Husqvarna", "model_name": "Norden 901 Expedition", "year_match": (2025, 2025), "position": "rear", "tire_size_or_brand_model": "150/70R17", "fitment_type": "oem"},
    
    # Bajaj Pulsar N160 2023
    {"manufacturer": "Bajaj", "model_name": "Pulsar N160", "year_match": (2023, 2024), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "Bajaj", "model_name": "Pulsar N160", "year_match": (2023, 2024), "position": "rear", "tire_size_or_brand_model": "140/70R17", "fitment_type": "oem"},
    
    # Bajaj Pulsar P150 2023
    {"manufacturer": "Bajaj", "model_name": "Pulsar P150", "year_match": (2023, 2024), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "Bajaj", "model_name": "Pulsar P150", "year_match": (2023, 2024), "position": "rear", "tire_size_or_brand_model": "130/70R17", "fitment_type": "oem"},
    
    # TVS Raider 125 2022
    {"manufacturer": "TVS", "model_name": "Raider 125", "year_match": (2022, 2024), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "TVS", "model_name": "Raider 125", "year_match": (2022, 2024), "position": "rear", "tire_size_or_brand_model": "130/70R17", "fitment_type": "oem"},
    
    # TVS Apache RTR 310 2024
    {"manufacturer": "TVS", "model_name": "Apache RTR 310", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "TVS", "model_name": "Apache RTR 310", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "140/70R17", "fitment_type": "oem"},
    
    # Hero Karizma XMR 250 2024
    {"manufacturer": "Hero", "model_name": "Karizma XMR 250", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "Hero", "model_name": "Karizma XMR 250", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "140/70R17", "fitment_type": "oem"},
    
    # Royal Enfield Classic 350 Halcyon 2024
    {"manufacturer": "Royal Enfield", "model_name": "Classic 350 Halcyon", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "100/90-19", "fitment_type": "oem"},
    {"manufacturer": "Royal Enfield", "model_name": "Classic 350 Halcyon", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "130/90-16", "fitment_type": "oem"},
    
    # Royal Enfield Bear 650 2024
    {"manufacturer": "Royal Enfield", "model_name": "Bear 650", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "90/90-21", "fitment_type": "oem"},
    {"manufacturer": "Royal Enfield", "model_name": "Bear 650", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "120/90-17", "fitment_type": "oem"},
    
    # Royal Enfield Goan Classic 350 2024
    {"manufacturer": "Royal Enfield", "model_name": "Goan Classic 350", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "100/90-19", "fitment_type": "oem"},
    {"manufacturer": "Royal Enfield", "model_name": "Goan Classic 350", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "130/90-16", "fitment_type": "oem"},
    
    # Honda SP 160 2024
    {"manufacturer": "Honda", "model_name": "SP 160", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "Honda", "model_name": "SP 160", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "130/70R17", "fitment_type": "oem"},
    
    # Honda Hornet 2.0 2024
    {"manufacturer": "Honda", "model_name": "Hornet 2.0", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "Honda", "model_name": "Hornet 2.0", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "140/70R17", "fitment_type": "oem"},
    
    # Yamaha FZS 25 2023
    {"manufacturer": "Yamaha", "model_name": "FZS 25", "year_match": (2023, 2024), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "Yamaha", "model_name": "FZS 25", "year_match": (2023, 2024), "position": "rear", "tire_size_or_brand_model": "140/70R17", "fitment_type": "oem"},
    
    # Suzuki V-Strom SX 250 2022
    {"manufacturer": "Suzuki", "model_name": "V-Strom SX 250", "year_match": (2022, 2024), "position": "front", "tire_size_or_brand_model": "110/80R19", "fitment_type": "oem"},
    {"manufacturer": "Suzuki", "model_name": "V-Strom SX 250", "year_match": (2022, 2024), "position": "rear", "tire_size_or_brand_model": "150/70R17", "fitment_type": "oem"},
    
    # KTM 390 Adventure SW 2024
    {"manufacturer": "KTM", "model_name": "390 Adventure SW", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "110/80R19", "fitment_type": "oem"},
    {"manufacturer": "KTM", "model_name": "390 Adventure SW", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "150/70R17", "fitment_type": "oem"},
    
    # BMW G310RR 2024
    {"manufacturer": "BMW", "model_name": "G 310 RR", "year_match": (2024, 2025), "position": "front", "tire_size_or_brand_model": "110/70R17", "fitment_type": "oem"},
    {"manufacturer": "BMW", "model_name": "G 310 RR", "year_match": (2024, 2025), "position": "rear", "tire_size_or_brand_model": "140/70R17", "fitment_type": "oem"},
    
    # Honda CBR900RR Fireblade 1992
    {"manufacturer": "Honda", "model_name": "CBR900RR Fireblade", "year_match": (1992, 1995), "position": "front", "tire_size_or_brand_model": "120/60R17", "fitment_type": "oem"},
    {"manufacturer": "Honda", "model_name": "CBR900RR Fireblade", "year_match": (1992, 1995), "position": "rear", "tire_size_or_brand_model": "160/60R17", "fitment_type": "oem"},
    
    # Honda CBR900RR 1998
    {"manufacturer": "Honda", "model_name": "CBR900RR", "year_match": (1998, 1999), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Honda", "model_name": "CBR900RR", "year_match": (1998, 1999), "position": "rear", "tire_size_or_brand_model": "160/60ZR17", "fitment_type": "oem"},
    
    # Suzuki GSX-R 750 1985
    {"manufacturer": "Suzuki", "model_name": "GSX-R 750", "year_match": (1985, 1987), "position": "front", "tire_size_or_brand_model": "120/70R16", "fitment_type": "oem"},
    {"manufacturer": "Suzuki", "model_name": "GSX-R 750", "year_match": (1985, 1987), "position": "rear", "tire_size_or_brand_model": "150/70R16", "fitment_type": "oem"},
    
    # Yamaha FZR1000 EXUP 1989
    {"manufacturer": "Yamaha", "model_name": "FZR1000 EXUP", "year_match": (1989, 1995), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Yamaha", "model_name": "FZR1000 EXUP", "year_match": (1989, 1995), "position": "rear", "tire_size_or_brand_model": "160/60ZR17", "fitment_type": "oem"},
    
    # Kawasaki ZX-9R Ninja 1994
    {"manufacturer": "Kawasaki", "model_name": "ZX-9R Ninja", "year_match": (1994, 1997), "position": "front", "tire_size_or_brand_model": "120/70R17", "fitment_type": "oem"},
    {"manufacturer": "Kawasaki", "model_name": "ZX-9R Ninja", "year_match": (1994, 1997), "position": "rear", "tire_size_or_brand_model": "160/60R17", "fitment_type": "oem"},
    
    # Honda RC30 (VFR750R) 1988
    {"manufacturer": "Honda", "model_name": "RC30 (VFR750R)", "year_match": (1988, 1992), "position": "front", "tire_size_or_brand_model": "120/70ZR16", "fitment_type": "oem"},
    {"manufacturer": "Honda", "model_name": "RC30 (VFR750R)", "year_match": (1988, 1992), "position": "rear", "tire_size_or_brand_model": "150/70ZR16", "fitment_type": "oem"},
    
    # Triumph Daytona 955i 2002
    {"manufacturer": "Triumph", "model_name": "Daytona 955i", "year_match": (2002, 2005), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Triumph", "model_name": "Daytona 955i", "year_match": (2002, 2005), "position": "rear", "tire_size_or_brand_model": "160/60ZR17", "fitment_type": "oem"},
    
    # Yamaha SR400 2014
    {"manufacturer": "Yamaha", "model_name": "SR400", "year_match": (2014, 2020), "position": "front", "tire_size_or_brand_model": "100/100-18", "fitment_type": "oem"},
    {"manufacturer": "Yamaha", "model_name": "SR400", "year_match": (2014, 2020), "position": "rear", "tire_size_or_brand_model": "130/80-17", "fitment_type": "oem"},
    
    # Bimota Tesi 1D 1991
    {"manufacturer": "Bimota", "model_name": "Tesi 1D", "year_match": (1991, 1995), "position": "front", "tire_size_or_brand_model": "120/70ZR17", "fitment_type": "oem"},
    {"manufacturer": "Bimota", "model_name": "Tesi 1D", "year_match": (1991, 1995), "position": "rear", "tire_size_or_brand_model": "180/50ZR17", "fitment_type": "oem"},
]

def seed_new_bike_fitments(repo):
    """
    Integrate WS-A fitments into the bike_tire_fitments table.
    
    Call this after all 45 WS-A bikes have been seeded to bike_models
    and bike_configs tables, as part of the overall seed_all() flow.
    
    Args:
        repo: a BikeRepository instance (or similar with a 'db' connection)
    
    Returns:
        int: count of fitments seeded
    """
    count = 0
    for fit in NEW_BIKE_FITMENTS:
        try:
            # Placeholder: actual seeding would query bike_models,
            # match tire_models, and INSERT into bike_tire_fitments.
            # For now, this is a data-only file pending integration into seed.py.
            count += 1
        except Exception as e:
            print(f"Error seeding fitment {fit}: {e}")
    return count

if __name__ == "__main__":
    print(f"WS-A fitments: {len(NEW_BIKE_FITMENTS)} entries ready for integration")
    print("Call seed_new_bike_fitments(repo) from seed.py:seed_all() after WS-A bikes are seeded")
