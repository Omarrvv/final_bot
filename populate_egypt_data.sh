#!/bin/bash
# populate_egypt_data.sh - Script to populate Egypt tourism chatbot data

# Print colored output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}  Egypt Tourism Chatbot Data Population  ${NC}"
echo -e "${YELLOW}=========================================${NC}"

# Create the scripts directory if it doesn't exist
if [ ! -d "./scripts/data_population" ]; then
    echo -e "${YELLOW}Creating data population scripts directory...${NC}"
    mkdir -p ./scripts/data_population
fi

# Copy the population scripts
echo -e "${YELLOW}Creating data population scripts...${NC}"

# Create populate_cities.py
cat > ./scripts/data_population/populate_cities.py << 'EOF'
# populate_cities.py
import json
import os
from datetime import datetime

# Ensure directories exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir("./data/cities")

# Define city data
cities = [
    {
        "id": "cairo",
        "name": {
            "en": "Cairo",
            "ar": "القاهرة"
        },
        "region": {
            "en": "Greater Cairo",
            "ar": "القاهرة الكبرى"
        },
        "coordinates": {
            "latitude": 30.0444,
            "longitude": 31.2357
        },
        "description": {
            "en": "Cairo, Egypt's sprawling capital, is set on the Nile River. At its heart is Tahrir Square and the vast Egyptian Museum, a trove of antiquities including the royal mummies and gilded King Tutankhamun artifacts. Nearby, Giza is home to the iconic pyramids and Great Sphinx, dating to the 26th century BC. In Gezira Island's leafy Zamalek district, 187m Cairo Tower affords panoramic city views.",
            "ar": "القاهرة، عاصمة مصر المترامية الأطراف، تقع على نهر النيل. في قلبها ميدان التحرير والمتحف المصري الكبير، وهو كنز من الآثار بما في ذلك المومياوات الملكية والقطع الأثرية المذهبة للملك توت عنخ آمون. وبالقرب منها، توجد الجيزة موطن الأهرامات الشهيرة وأبو الهول العظيم، التي يعود تاريخها إلى القرن السادس والعشرين قبل الميلاد. وفي حي الزمالك بجزيرة الجزيرة المورقة، يوفر برج القاهرة البالغ ارتفاعه 187 متراً إطلالات بانورامية على المدينة."
        },
        "history": {
            "en": "Founded in 969 CE by the Fatimid dynasty, Cairo has been the capital of Egypt for over a thousand years. The city has been a center of political, cultural, and religious importance throughout its history. Cairo's historic core was designated a UNESCO World Heritage Site in 1979.",
            "ar": "تأسست القاهرة عام 969 ميلادياً على يد الدولة الفاطمية، وكانت عاصمة مصر لأكثر من ألف عام. كانت المدينة مركزاً للأهمية السياسية والثقافية والدينية طوال تاريخها. تم تصنيف نواة القاهرة التاريخية كموقع للتراث العالمي لليونسكو في عام 1979."
        },
        "practical_info": {
            "population": 21323000,
            "area": 3085,
            "timezone": "EET (UTC+2)",
            "language": "Arabic",
            "currency": "Egyptian Pound (EGP)",
            "weather": "Hot desert climate with mild winters and hot summers. Rainfall is rare.",
            "best_time_to_visit": "October to April, when temperatures are milder",
            "transportation": {
                "en": "Cairo has an extensive public transportation system including metro lines, buses, taxis, and ride-sharing services. The Cairo Metro is the most efficient way to navigate the city, especially during rush hours. Taxis and ride-sharing services like Uber and Careem are widely available.",
                "ar": "تمتلك القاهرة نظام نقل عام واسع يشمل خطوط المترو والحافلات وسيارات الأجرة وخدمات مشاركة الركوب. يعد مترو القاهرة أكثر الطرق كفاءة للتنقل في المدينة، خاصة خلال ساعات الذروة. تتوفر سيارات الأجرة وخدمات مشاركة الركوب مثل أوبر وكريم على نطاق واسع."
            }
        },
        "highlights": [
            {
                "id": "pyramids_of_giza",
                "name": {
                    "en": "Pyramids of Giza",
                    "ar": "أهرامات الجيزة"
                }
            },
            {
                "id": "egyptian_museum",
                "name": {
                    "en": "Egyptian Museum",
                    "ar": "المتحف المصري"
                }
            },
            {
                "id": "khan_el_khalili",
                "name": {
                    "en": "Khan El-Khalili",
                    "ar": "خان الخليلي"
                }
            },
            {
                "id": "cairo_citadel",
                "name": {
                    "en": "Cairo Citadel",
                    "ar": "قلعة صلاح الدين"
                }
            },
            {
                "id": "al_azhar_park",
                "name": {
                    "en": "Al-Azhar Park",
                    "ar": "حديقة الأزهر"
                }
            }
        ],
        "images": [
            "cairo_skyline.jpg",
            "cairo_downtown.jpg",
            "cairo_nile_view.jpg"
        ],
        "tags": ["capital", "urban", "historical", "pyramids", "museums", "nile"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "luxor",
        "name": {
            "en": "Luxor",
            "ar": "الأقصر"
        },
        "region": {
            "en": "Upper Egypt",
            "ar": "صعيد مصر"
        },
        "coordinates": {
            "latitude": 25.6872,
            "longitude": 32.6396
        },
        "description": {
            "en": "Luxor is a city in Upper Egypt and the capital of Luxor Governorate. The city is located on the east bank of the Nile River and was the ancient Egyptian city of Thebes, the glorious capital of Egypt during the New Kingdom. Luxor has frequently been called the 'world's greatest open-air museum', with ruins of temple complexes at Karnak and Luxor, and the Valley of the Kings and Valley of the Queens on the opposite bank of the Nile.",
            "ar": "الأقصر هي مدينة في صعيد مصر وعاصمة محافظة الأقصر. تقع المدينة على الضفة الشرقية لنهر النيل وكانت مدينة طيبة المصرية القديمة، العاصمة المجيدة لمصر خلال المملكة الحديثة. غالبًا ما كانت الأقصر تسمى \"أعظم متحف مفتوح في العالم\"، مع أطلال مجمعات المعابد في الكرنك والأقصر، ووادي الملوك ووادي الملكات على الضفة المقابلة للنيل."
        },
        "history": {
            "en": "Luxor was the ancient city of Thebes, the great capital of Upper Egypt during the New Kingdom. The city was dedicated to the god Amun, and was the location of the annual Opet Festival. The earliest monuments in Luxor date back to the Eleventh Dynasty of Egypt, when the city was called Wsit (\"City\") and was the capital of Upper Egypt.",
            "ar": "كانت الأقصر المدينة القديمة طيبة، العاصمة العظيمة لصعيد مصر خلال المملكة الحديثة. كانت المدينة مكرسة للإله آمون، وكانت موقع مهرجان أوبت السنوي. تعود أقدم المعالم في الأقصر إلى الأسرة الحادية عشرة المصرية، عندما كانت تسمى المدينة وسيت (\"المدينة\") وكانت عاصمة صعيد مصر."
        },
        "practical_info": {
            "population": 507000,
            "area": 416,
            "timezone": "EET (UTC+2)",
            "language": "Arabic",
            "currency": "Egyptian Pound (EGP)",
            "weather": "Hot desert climate. Very hot summers and mild winters. Almost no rainfall throughout the year.",
            "best_time_to_visit": "October to April, to avoid the extreme summer heat",
            "transportation": {
                "en": "Luxor is compact enough to walk around the east bank, but to visit the many sites on the west bank you'll need transportation. Options include taxis, horse-drawn carriages (calèches), boats to cross the Nile, and organized tours. Bicycle rental is also popular for exploring the west bank.",
                "ar": "الأقصر صغيرة بما يكفي للتجول في الضفة الشرقية سيراً على الأقدام، ولكن لزيارة المواقع العديدة في الضفة الغربية ستحتاج إلى وسيلة نقل. تشمل الخيارات سيارات الأجرة والعربات التي تجرها الخيول (الحنطور) والقوارب لعبور النيل والجولات المنظمة. يعد استئجار الدراجات شائعًا أيضًا لاستكشاف الضفة الغربية."
            }
        },
        "highlights": [
            {
                "id": "karnak_temple",
                "name": {
                    "en": "Karnak Temple",
                    "ar": "معبد الكرنك"
                }
            },
            {
                "id": "luxor_temple",
                "name": {
                    "en": "Luxor Temple",
                    "ar": "معبد الأقصر"
                }
            },
            {
                "id": "valley_of_kings",
                "name": {
                    "en": "Valley of the Kings",
                    "ar": "وادي الملوك"
                }
            },
            {
                "id": "hatshepsut_temple",
                "name": {
                    "en": "Temple of Hatshepsut",
                    "ar": "معبد حتشبسوت"
                }
            },
            {
                "id": "luxor_museum",
                "name": {
                    "en": "Luxor Museum",
                    "ar": "متحف الأقصر"
                }
            }
        ],
        "images": [
            "luxor_aerial.jpg",
            "karnak_temple.jpg",
            "valley_of_kings.jpg"
        ],
        "tags": ["ancient", "temples", "tombs", "historical", "nile", "archaeology"],
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": "aswan",
        "name": {
            "en": "Aswan",
            "ar": "أسوان"
        },
        "region": {
            "en": "Upper Egypt",
            "ar": "صعيد مصر"
        },
        "coordinates": {
            "latitude": 24.0889,
            "longitude": 32.8998
        },
        "description": {
            "en": "Aswan is a city in the south of Egypt, the capital of the Aswan Governorate. It stands on the east bank of the Nile at the first cataract and is a busy market and tourist center. Aswan is considered the southern gateway to Egypt and has a more African atmosphere than other Egyptian cities. The pace of life is slower, the air is cleaner, and the city is famous for its beautiful Nile setting with feluccas sailing around the small islands.",
            "ar": "أسوان هي مدينة في جنوب مصر، عاصمة محافظة أسوان. تقع على الضفة الشرقية للنيل عند الشلال الأول وهي مركز سوق وسياحة مزدحم. تعتبر أسوان البوابة الجنوبية لمصر ولديها أجواء أفريقية أكثر من المدن المصرية الأخرى. وتيرة الحياة أبطأ، والهواء أنظف، والمدينة مشهورة بموقعها الجميل على النيل مع المراكب الشراعية التي تبحر حول الجزر الصغيرة."
        },
        "history": {
            "en": "Aswan has been southern Egypt's strategic and commercial gateway since antiquity, controlling the trade routes from Nubia to the north. It was also important for the stone quarries that supplied granite for obelisks and sculptures throughout ancient Egypt. During Greco-Roman times, it was a military outpost and was known as Syene.",
            "ar": "كانت أسوان بوابة جنوب مصر الاستراتيجية والتجارية منذ العصور القديمة، حيث تسيطر على طرق التجارة من النوبة إلى الشمال. كانت أيضًا مهمة لمحاجر الحجارة التي زودت الجرانيت للمسلات والمنحوتات في جميع أنحاء مصر القديمة. خلال العصور اليونانية الرومانية، كانت موقعًا عسكريًا وكانت تعرف باسم سيينه."
        },
        "practical_info": {
            "population": 290000,
            "area": 34.6,
            "timezone": "EET (UTC+2)",
            "language": "Arabic",
            "currency": "Egyptian Pound (EGP)",
            "weather": "Hot desert climate. Very hot summers and warm winters. Almost no rainfall throughout the year. Considered one of the sunniest places on Earth.",
            "best_time_to_visit": "October to April, when temperatures are more comfortable",
            "transportation": {
                "en": "Aswan is small enough to explore on foot, particularly around the Corniche area. Taxis and horse-drawn carriages are available for longer journeys. Ferries cross to Elephantine Island regularly, and feluccas can be hired for trips on the Nile. For trips to nearby attractions like Abu Simbel, organized tours or private drivers are the best options.",
                "ar": "أسوان صغيرة بما يكفي لاستكشافها سيراً على الأقدام، خاصة حول منطقة الكورنيش. تتوفر سيارات الأجرة والعربات التي تجرها الخيول للرحلات الأطول. تعبر العبارات إلى جزيرة الفنتين بانتظام، ويمكن استئجار المراكب الشراعية للرحلات على النيل. بالنسبة للرحلات إلى المعالم السياحية القريبة مثل أبو سمبل، فإن الجولات المنظمة أو السائقين الخاصين هي الخيارات الأفضل."
            }
        },
        "highlights": [
            {
                "id": "philae_temple",
                "name": {
                    "en": "Temple of Philae",
                    "ar": "معبد فيلة"
                }
            },
            {
                "id": "abu_simbel",
                "name": {
                    "en": "Abu Simbel Temples",
                    "ar": "معابد أبو سمبل"
                }
            },
            {
                "id": "unfinished_obelisk",
                "name": {
                    "en": "Unfinished Obelisk",
                    "ar": "المسلة الناقصة"
                }
            },
            {
                "id": "elephantine_island",
                "name": {
                    "en": "Elephantine Island",
                    "ar": "جزيرة الفنتين"
                }
            },
            {
                "id": "nubian_museum",
                "name": {
                    "en": "Nubian Museum",
                    "ar": "المتحف النوبي"
                }
            }
        ],
        "images": [
            "aswan_nile.jpg",
            "philae_temple.jpg",
            "nubian_village.jpg"
        ],
        "tags": ["nile", "nubian", "temples", "islands", "dam", "relaxing"],
        "last_updated": datetime.now().isoformat()
    }
]

# Save cities to JSON files
for city in cities:
    with open(f"./data/cities/{city['id']}.json", 'w', encoding='utf-8') as f:
        json.dump(city, f, ensure_ascii=False, indent=2)
    print(f"Created city data for {city['name']['en']}")

print("City data population complete!")
EOF
echo -e "${GREEN}✓ Created populate_cities.py${NC}"

# Create populate_data.py (main script)
cat > ./scripts/data_population/populate_data.py << 'EOF'
#!/usr/bin/env python3
# populate_data.py - Main script to populate the Egypt tourism chatbot database

import os
import json
import importlib.util
import subprocess
import time
from datetime import datetime

def log_message(message):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        log_message(f"Created directory: {directory}")

def run_script(script_name):
    """Run a Python script and return its output"""
    log_message(f"Running {script_name}...")
    
    try:
        # Use subprocess to run the script
        result = subprocess.run(['python', f'./scripts/data_population/{script_name}'], 
                               capture_output=True, text=True, check=True)
        
        log_message(f"Successfully completed {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Error running {script_name}: {e}")
        log_message(f"Output: {e.output}")
        log_message(f"Error: {e.stderr}")
        return False

def create_index_file():
    """Create an index file with metadata about all available data"""
    log_message("Creating data index file...")
    
    index = {
        "last_updated": datetime.now().isoformat(),
        "categories": {},
        "entity_count": 0
    }
    
    # Scan all directories in the data folder
    for category in os.listdir("./data"):
        category_path = os.path.join("./data", category)
        
        # Skip if not a directory or hidden
        if not os.path.isdir(category_path) or category.startswith('.') or category == "sessions":
            continue
        
        # Create category entry
        index["categories"][category] = {
            "count": 0,
            "entities": []
        }
        
        # Scan all files in the category
        for filename in os.listdir(category_path):
            if not filename.endswith('.json') or filename.startswith('.'):
                continue
                
            file_path = os.path.join(category_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract entity info
                entity_info = {
                    "id": data.get("id", filename.replace(".json", "")),
                    "name": data.get("name", {}).get("en", "Unknown"),
                    "file": filename,
                    "type": data.get("type", "unknown")
                }
                
                # Add to index
                index["categories"][category]["entities"].append(entity_info)
                index["categories"][category]["count"] += 1
                index["entity_count"] += 1
                
            except Exception as e:
                log_message(f"Error processing {file_path}: {e}")
    
    # Write index file
    with open("./data/index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    log_message(f"Index file created with {index['entity_count']} entities across {len(index['categories'])} categories")
    return index

def main():
    """Main function to execute data population"""
    start_time = time.time()
    log_message("Starting Egypt Tourism Chatbot data population")
    
    # Create the data population directory if it doesn't exist
    ensure_dir("./scripts/data_population")
    
    # Create necessary data directories
    data_directories = [
        "./data/schemas",
        "./data/attractions",
        "./data/attractions/historical",
        "./data/attractions/cultural",
        "./data/attractions/religious",
        "./data/attractions/natural",
        "./data/attractions/modern",
        "./data/attractions/shopping",
        "./data/cities",
        "./data/accommodations",
        "./data/restaurants",
        "./data/transportation",
        "./data/tours",
        "./data/practical_info",
        "./data/events",
        "./data/media"
    ]
    
    for directory in data_directories:
        ensure_dir(directory)
    
    # List of scripts to run
    scripts = [
        "populate_cities.py",
        "populate_attractions.py",
        "populate_restaurants.py",
        "populate_accommodations.py",
        "populate_transportation.py"
    ]
    
    # Run each script
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
    
    # Create index file
    index = create_index_file()
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    log_message(f"Data population completed in {duration:.2f} seconds")
    log_message(f"Successfully ran {success_count}/{len(scripts)} scripts")
    log_message(f"Created {index['entity_count']} entities across {len(index['categories'])} categories")
    
    # Instructions for next steps
    log_message("\nNext steps:")
    log_message("1. Check the data directories for accuracy")
    log_message("2. Update your chatbot to use the new data")
    log_message("3. Consider adding more data to improve coverage")
    log_message("4. Implement database migration if needed")

if __name__ == "__main__":
    main()
EOF
echo -e "${GREEN}✓ Created populate_data.py${NC}"

# Make the main scripts executable
chmod +x ./scripts/data_population/populate_data.py

# Create data directories
echo -e "${YELLOW}Creating data directories...${NC}"
mkdir -p ./data/schemas
mkdir -p ./data/attractions/historical
mkdir -p ./data/attractions/cultural
mkdir -p ./data/attractions/religious
mkdir -p ./data/attractions/natural
mkdir -p ./data/attractions/modern
mkdir -p ./data/attractions/shopping
mkdir -p ./data/cities
mkdir -p ./data/accommodations
mkdir -p ./data/restaurants
mkdir -p ./data/transportation
mkdir -p ./data/tours
mkdir -p ./data/practical_info
mkdir -p ./data/events
mkdir -p ./data/media
echo -e "${GREEN}✓ Created data directories${NC}"

# Run the main population script
echo -e "${YELLOW}Running data population script...${NC}"
echo -e "${YELLOW}This will populate the cities data as a starting point.${NC}"
echo -e "${YELLOW}Note: For complete population, download all script files from your project.${NC}"

# Run the script
python ./scripts/data_population/populate_cities.py

echo -e "${GREEN}✓ Basic data population completed!${NC}"
echo -e "${YELLOW}---------------------------------------${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Add the remaining population scripts to the data_population directory:"
echo -e "   - populate_attractions.py"
echo -e "   - populate_restaurants.py"
echo -e "   - populate_accommodations.py"
echo -e "   - populate_transportation.py"
echo -e "2. Run the main script: python ./scripts/data_population/populate_data.py"
echo -e "3. Check your data and update your chatbot to use it"
echo -e "${YELLOW}---------------------------------------${NC}"
