"""
Egypt Tourism Knowledge Base.
Structured information about Egyptian tourism, organized by categories.
"""
from typing import Dict, Any

class TourismKnowledgeBase:
    def __init__(self):
        self._data = {
            "general": self._load_general_info(),
            "attractions": self._load_attractions(),
            "cuisine": self._load_cuisine(),
            "travel_tips": self._load_travel_tips(),
            "history": self._load_history(),
            "culture": self._load_culture(),
            "cities": self._load_cities(),
            "accommodation": self._load_accommodation(),
            "activities": self._load_activities(),
            "faq": self._load_faq()
        }

    def get_category(self, category: str) -> Dict[str, Any]:
        """Get information for a specific category."""
        return self._data.get(category, {})

    def get_topic(self, category: str, topic: str) -> str:
        """Get specific topic information within a category."""
        return self._data.get(category, {}).get(topic, "")

    @staticmethod
    def _load_general_info() -> Dict[str, str]:
        return {
            "greeting": "Welcome to Egypt! I'm your virtual guide to the land of the pharaohs. How can I help you today?",
            "about": "Egypt is a country in North Africa with a history spanning over 5000 years. Home to ancient wonders like the pyramids and temples, as well as beautiful beaches along the Red Sea. Egypt offers a unique blend of ancient history, vibrant culture, and modern attractions.",
            "best_time": "The best time to visit Egypt is from October to April when the temperature is cooler. Summer months (June-August) can be extremely hot, especially in Upper Egypt, with temperatures often exceeding 40°C (104°F). Winter (December-February) is peak tourist season with pleasant temperatures.",
            "visa": "Most visitors to Egypt need a visa. Tourist visas can be obtained online through the e-visa portal, on arrival at Egyptian airports, or from Egyptian embassies abroad. The standard tourist visa is valid for 30 days.",
            "language": "Arabic is the official language of Egypt. English is widely spoken in tourist areas, hotels, and restaurants. Learning a few basic Arabic phrases can enhance your experience.",
            "religion": "Islam is the predominant religion in Egypt, with about 90% of the population being Muslim. Coptic Christianity is the largest minority religion. Religious sites of both faiths are important cultural attractions.",
            "geography": "Egypt spans two continents, with the Sinai Peninsula in Asia and the rest of the country in Africa. The Nile River, the world's longest river, runs through Egypt from south to north, creating a fertile valley amid desert landscapes."
        }

    @staticmethod
    def _load_attractions() -> Dict[str, str]:
        return {
            "pyramids": "The Pyramids of Giza are Egypt's most iconic monuments, built over 4,500 years ago as tombs for the pharaohs. The complex includes the Great Pyramid of Khufu (one of the Seven Wonders of the Ancient World), the Pyramid of Khafre, the Pyramid of Menkaure, and the Great Sphinx. Located just outside Cairo, they are a must-visit destination.",
            "luxor": "Luxor is home to the Valley of the Kings and the magnificent Karnak Temple complex. Often called the world's greatest open-air museum, Luxor contains nearly one-third of the world's ancient monuments. Key sites include Luxor Temple, Karnak Temple, Valley of the Kings (where Tutankhamun's tomb was discovered), Valley of the Queens, and the Colossi of Memnon.",
            "alexandria": "Alexandria, founded by Alexander the Great, features the modern Library of Alexandria (Bibliotheca Alexandrina) and ancient Roman ruins. This Mediterranean coastal city offers a different atmosphere from the rest of Egypt, with Greco-Roman landmarks, beautiful beaches, and a cosmopolitan heritage.",
            "abu_simbel": "Abu Simbel consists of two massive rock temples in southern Egypt, built by Pharaoh Ramses II. The temples were relocated in the 1960s to avoid being submerged during the creation of Lake Nasser. The main temple features four colossal statues of Ramses II at the entrance and is aligned so that twice a year, the sun illuminates the inner sanctuary.",
            "aswan": "Aswan is a scenic city on the Nile with ancient quarries, the Unfinished Obelisk, Philae Temple, and the Aswan High Dam. The city offers a more relaxed atmosphere than Cairo or Luxor, with beautiful Nile views and Nubian villages nearby.",
            "red_sea": "The Red Sea coast offers world-class diving and snorkeling with vibrant coral reefs and diverse marine life. Popular resort towns include Sharm El Sheikh, Hurghada, and Marsa Alam, offering luxury resorts, water sports, and desert excursions.",
            "white_desert": "The White Desert National Park features surreal chalk rock formations that resemble an alien landscape. Created through erosion, these unusual shapes include structures resembling mushrooms, camels, and other forms. Popular for overnight camping under the stars.",
            "siwa_oasis": "Siwa Oasis is a remote desert oasis with freshwater springs, ancient mud-brick fortresses, and unique Berber culture. Located near the Libyan border, it's famous for the Oracle Temple where Alexander the Great was declared a god.",
            "st_catherine": "Saint Catherine's Monastery at the foot of Mount Sinai is one of the oldest working Christian monasteries in the world. It houses a significant collection of early Christian manuscripts and icons. Many visitors climb Mount Sinai for sunrise views.",
            "cairo_museum": "The Egyptian Museum in Cairo houses the world's largest collection of Pharaonic antiquities, including treasures from Tutankhamun's tomb. The new Grand Egyptian Museum near the Pyramids of Giza is set to become the largest archaeological museum in the world.",
            "khan_el_khalili": "Khan El Khalili is Cairo's famous bazaar, dating back to the 14th century. This labyrinthine market offers everything from spices and perfumes to handcrafted jewelry, textiles, and souvenirs. It's also home to historic cafés like El Fishawi, which has been operating continuously for over 200 years.",
            "nile_cruise": "A Nile cruise between Luxor and Aswan is a popular way to see multiple ancient sites while enjoying the scenic river landscape. Most cruises stop at Edfu (Temple of Horus) and Kom Ombo (Temple of Sobek) along the way."
        }

    @staticmethod
    def _load_cuisine() -> Dict[str, str]:
        return {
            "general": "Egyptian cuisine offers flavorful dishes with influences from the Mediterranean, Middle East, and North Africa. Food is an important part of Egyptian culture and social life, with meals often being communal experiences.",
            "koshari": "Koshari is Egypt's national dish, a comforting mix of rice, lentils, pasta, chickpeas, topped with crispy fried onions and tangy tomato sauce. This vegetarian street food is available everywhere from simple carts to upscale restaurants.",
            "ful_medames": "Ful Medames is a staple Egyptian breakfast dish made of slow-cooked fava beans seasoned with olive oil, lemon juice, and cumin. Often served with Egyptian bread (aish baladi), hard-boiled eggs, and fresh vegetables.",
            "molokhia": "Molokhia is a popular green soup made from jute leaves, typically served with chicken or rabbit and rice. This distinctive dish has a somewhat viscous texture and is flavored with garlic and coriander.",
            "kofta": "Kofta consists of grilled minced meat (usually beef or lamb) mixed with spices and formed into cylinders. Often served with rice, bread, and tahini sauce.",
            "shawarma": "Shawarma is thinly sliced marinated meat (chicken, beef, or lamb) cooked on a vertical rotisserie and served in bread with tahini, vegetables, and pickles.",
            "ta'ameya": "Ta'ameya is the Egyptian version of falafel, made with fava beans instead of chickpeas. These crispy, green-interior fritters are a popular street food served in bread with tahini and vegetables.",
            "feteer": "Feteer is a flaky layered pastry that can be served sweet (with honey, sugar, or fruit) or savory (with cheese, meat, or vegetables). It's sometimes called 'Egyptian pizza.'",
            "desserts": "Egyptian desserts often feature phyllo dough, nuts, and sweet syrups. Popular options include baklava, basbousa (semolina cake), konafa (shredded phyllo with sweet cheese filling), and umm ali (bread pudding with nuts and raisins).",
            "beverages": "Traditional Egyptian beverages include karkade (hibiscus tea, served hot or cold), sahlab (thick, sweet winter drink), fresh fruit juices, and strong Turkish-style coffee. Tea with mint is the most common everyday drink."
        }

    @staticmethod
    def _load_travel_tips() -> Dict[str, str]:
        return {
            "safety": "Egypt is generally safe for tourists. Stay aware of your surroundings and follow local customs and advice. Tourist areas have increased security presence. It's advisable to check your government's travel advisories before visiting and avoid border regions and the North Sinai.",
            "transportation": "Major cities are connected by flights and trains. Within cities, use official taxis or ride-sharing apps like Uber and Careem. The Cairo Metro is efficient for getting around the capital. For longer distances, consider domestic flights to save time, as road journeys can be lengthy.",
            "currency": "The Egyptian Pound (EGP) is the local currency. Major hotels and restaurants accept credit cards, but smaller establishments and markets often prefer cash. ATMs are widely available in cities and tourist areas. It's advisable to carry small denominations for tipping and small purchases.",
            "dress_code": "Egypt is a conservative country. While tourist areas are more relaxed, it's respectful to dress modestly, especially when visiting religious sites. Women should cover shoulders and knees, and men should avoid shorts in non-resort areas. In beach resorts like Sharm El Sheikh, Western-style beachwear is acceptable.",
            "tipping": "Tipping (baksheesh) is an important part of Egyptian culture. Service workers expect tips, including hotel staff, restaurant servers (10-15%), tour guides, and drivers. Small tips are also expected for services like helping with luggage or providing directions.",
            "bargaining": "Bargaining is expected in markets and with taxis without meters. Start by offering about 60-70% of the initial asking price. Keep the negotiation friendly and be prepared to walk away if you can't reach an agreement.",
            "photography": "Be respectful when taking photos of locals and always ask permission first. Many museums and some archaeological sites charge camera fees or prohibit photography altogether. Inside many tombs, photography is either prohibited or requires a special ticket.",
            "water": "Avoid drinking tap water. Bottled water is inexpensive and widely available. Be cautious with ice and raw vegetables in less touristy areas. Most reputable hotels and restaurants use filtered water for ice and food preparation.",
            "health": "No special vaccinations are required for Egypt, but it's recommended to be up-to-date on routine vaccines. Bring medication for stomach issues ('Pharaoh's Revenge'), sun protection, and insect repellent. Travel insurance with medical coverage is strongly advised.",
            "internet": "WiFi is available in most hotels, cafes, and restaurants in tourist areas. Local SIM cards with data plans are inexpensive and can be purchased at the airport or in mobile shops (passport required).",
            "electricity": "Egypt uses 220V with European-style two-pin round plugs (Type C). Adapters are easily found, but bring your own to be safe. Power outages can occur, though major hotels usually have generators."
        }

    @staticmethod
    def _load_history() -> Dict[str, str]:
        return {
            "ancient_egypt": "Ancient Egyptian civilization began around 3100 BCE with the unification of Upper and Lower Egypt under King Menes. It lasted for nearly 3,000 years through various dynasties until the Roman conquest in 30 BCE. This period saw the construction of the pyramids, the rule of famous pharaohs like Ramses II and Tutankhamun, and the development of hieroglyphic writing, advanced mathematics, and astronomy.",
            "middle_kingdom": "The Middle Kingdom (2055-1650 BCE) was a period of reunification and cultural flourishing after the First Intermediate Period. Literature, art, and architecture thrived, and trade expanded. Pharaohs of this period built monuments in Karnak and other sites.",
            "new_kingdom": "The New Kingdom (1550-1069 BCE) was Egypt's most prosperous and powerful period. It included famous rulers like Hatshepsut, Akhenaten, Tutankhamun, and Ramses II. This era saw the construction of the Valley of the Kings, Abu Simbel, and many temples at Luxor and Karnak.",
            "ptolemaic_period": "The Ptolemaic Period (332-30 BCE) began after Alexander the Great conquered Egypt. His general Ptolemy established a Greek dynasty that ruled Egypt for nearly 300 years. The last ruler was Cleopatra VII, who allied with Rome's Mark Antony before being defeated by Octavian (later Emperor Augustus).",
            "roman_byzantine": "Egypt became a Roman province after Cleopatra's defeat in 30 BCE. Later, it was part of the Byzantine Empire and became predominantly Christian. Many temples were converted to churches, and monasticism flourished in the desert.",
            "islamic_era": "Arab Muslims conquered Egypt in 641 CE, bringing Islam to the region. Egypt was ruled by various Islamic dynasties, including the Fatimids who founded Cairo in 969 CE. The Mamluk Sultanate (1250-1517) left many architectural treasures in Cairo.",
            "ottoman_period": "The Ottoman Empire conquered Egypt in 1517 and ruled until the early 19th century. During this period, Egypt was an important but semi-autonomous province, with Mamluk beys maintaining significant power.",
            "modern_egypt": "Modern Egypt began with Muhammad Ali Pasha, who seized power in 1805 and modernized the country. The Suez Canal opened in 1869, increasing Egypt's strategic importance. Britain occupied Egypt in 1882 and established a protectorate until 1922, when Egypt gained nominal independence. The monarchy was overthrown in 1952, and Egypt became a republic under Gamal Abdel Nasser."
        }

    @staticmethod
    def _load_culture() -> Dict[str, str]:
        return {
            "art": "Egyptian art spans thousands of years, from ancient tomb paintings and sculptures to modern works. Ancient Egyptian art was highly symbolic and followed strict conventions for depicting humans, gods, and nature. Contemporary Egyptian art blends traditional influences with modern styles and social commentary.",
            "music": "Egyptian music has deep historical roots and significant influence across the Arab world. Traditional instruments include the oud (lute), qanun (zither), and tabla (drum). Egypt produced many famous singers, including Umm Kulthum, whose monthly radio concerts would empty the streets as everyone listened. Modern Egyptian music ranges from classical Arabic to electronic shaabi and mahraganat.",
            "literature": "Egypt has a rich literary tradition dating back to ancient times. Modern Egyptian literature flourished in the 20th century with writers like Naguib Mahfouz (Nobel Prize winner), Taha Hussein, and Nawal El Saadawi. Cairo is a major publishing center for the Arab world.",
            "film": "Egypt has the oldest and largest film industry in the Arab world, often called 'Hollywood on the Nile.' The golden age of Egyptian cinema was from the 1940s to the 1960s, producing classics that are still beloved across the Arab world. The Cairo International Film Festival is one of the oldest film festivals in the Middle East.",
            "festivals": "Egypt celebrates numerous festivals throughout the year. Religious celebrations include Ramadan (month of fasting followed by Eid al-Fitr) and Coptic Christmas (January 7). Cultural festivals include the Abu Simbel Sun Festival (February and October), when sunlight illuminates specific statues in the temple, and Sham El-Nessim, an ancient spring festival celebrated by all Egyptians regardless of religion.",
            "crafts": "Traditional Egyptian crafts include papyrus making, alabaster carving, carpet weaving, pottery, and metalwork. These crafts have been practiced for thousands of years and make popular souvenirs. The Khan El Khalili bazaar in Cairo is a great place to see artisans at work and purchase handcrafted items.",
            "family_life": "Family is central to Egyptian society, with strong intergenerational bonds and responsibilities. Extended families often live together or near each other. Hospitality is a core value, and guests are treated with great generosity and respect."
        }

    @staticmethod
    def _load_cities() -> Dict[str, str]:
        return {
            "cairo": "Cairo is Egypt's sprawling capital and largest city, home to over 20 million people in its metropolitan area. It blends ancient history with modern urban life. Key attractions include the Pyramids of Giza, the Egyptian Museum, the Citadel of Saladin, Al-Azhar Mosque, and Khan El Khalili bazaar. Cairo offers vibrant nightlife, diverse dining, and shopping options from traditional markets to modern malls.",
            "luxor": "Luxor, the ancient city of Thebes, is often called the world's greatest open-air museum. The city is divided by the Nile, with the East Bank housing Luxor Temple and Karnak Temple, along with most hotels and restaurants. The West Bank contains the Valley of the Kings, Valley of the Queens, and numerous mortuary temples. Hot air balloon rides at sunrise offer spectacular views of the ancient sites.",
            "aswan": "Aswan is Egypt's southernmost city, with a more relaxed atmosphere and beautiful Nile scenery. Attractions include the Philae Temple, Unfinished Obelisk, Aswan High Dam, and Nubian villages. Elephantine Island in the middle of the Nile offers archaeological sites and colorful Nubian houses. Aswan is also the gateway to Abu Simbel.",
            "alexandria": "Alexandria is Egypt's second-largest city and main Mediterranean port, founded by Alexander the Great in 331 BCE. It offers a different atmosphere from the rest of Egypt, with Greco-Roman ruins, colonial architecture, and beautiful beaches. Key sites include the Bibliotheca Alexandrina, Qaitbay Citadel, Montazah Palace Gardens, and the Catacombs of Kom El Shoqafa.",
            "sharm_el_sheikh": "Sharm El Sheikh is a popular resort town on the southern tip of the Sinai Peninsula, known for its clear waters and coral reefs. It's a major diving and snorkeling destination, with access to sites like Ras Mohammed National Park and the Tiran Island reefs. The town offers luxury resorts, vibrant nightlife, and desert excursions.",
            "hurghada": "Hurghada is a Red Sea resort town known for its beautiful beaches and vibrant marine life. Originally a fishing village, it has developed into a major tourist destination with numerous resorts, restaurants, and nightlife options. Popular activities include diving, snorkeling, desert safaris, and boat trips to nearby islands.",
            "dahab": "Dahab is a laid-back coastal town on the Sinai Peninsula, popular with backpackers and diving enthusiasts. Once a Bedouin fishing village, it maintains a more relaxed atmosphere than Sharm El Sheikh. The Blue Hole, one of the world's most famous dive sites, is located nearby. Dahab also offers access to Mount Sinai and Saint Catherine's Monastery.",
            "marsa_alam": "Marsa Alam is a developing resort area on the Red Sea coast, known for its unspoiled beaches and marine life. It's less crowded than Hurghada and Sharm El Sheikh, offering a more tranquil experience. The area is famous for dolphin spotting at Samadai Reef (Dolphin House) and diving with dugongs and sea turtles."
        }

    @staticmethod
    def _load_accommodation() -> Dict[str, str]:
        return {
            "luxury_hotels": "Egypt offers world-class luxury accommodations, particularly in Cairo, Luxor, and Red Sea resorts. Historic properties include the Marriott Mena House (with pyramid views), the Old Cataract Hotel in Aswan (where Agatha Christie wrote 'Death on the Nile'), and the Winter Palace in Luxor. International chains like Four Seasons, Ritz-Carlton, and Sofitel maintain multiple properties throughout Egypt.",
            "mid_range": "Mid-range hotels are plentiful in all tourist areas, offering comfortable accommodations at reasonable prices. Many are operated by international chains like Hilton, Novotel, and Steigenberger. These hotels typically offer pools, restaurants, and basic amenities, making them popular with package tours and independent travelers alike.",
            "budget": "Budget travelers can find affordable options throughout Egypt. Cairo's downtown area has numerous budget hotels and hostels. In Luxor and Aswan, locally-owned hotels on the east bank offer basic rooms at low prices. Dahab is particularly known for its budget-friendly accommodations popular with backpackers.",
            "nile_cruises": "Nile cruises operate primarily between Luxor and Aswan, ranging from 3 to 7 nights. Vessels range from luxury floating hotels with pools and entertainment to more basic boats. Most cruises include guided tours of the major temples along the route, including Edfu, Kom Ombo, and Philae.",
            "desert_camps": "Desert camps offer unique accommodation experiences in locations like the White Desert, Siwa Oasis, and Sinai Peninsula. These range from basic Bedouin-style camps with mattresses under the stars to more comfortable 'glamping' setups with proper beds and facilities. Desert camps typically include meals and activities like sandboarding and stargazing.",
            "red_sea_resorts": "Red Sea destinations like Sharm El Sheikh, Hurghada, and Marsa Alam specialize in all-inclusive beach resorts. These self-contained properties offer multiple restaurants, pools, private beaches, and water sports facilities. Many cater to specific markets, with family-friendly, adults-only, and diving-focused options available."
        }

    @staticmethod
    def _load_activities() -> Dict[str, str]:
        return {
            "diving": "The Red Sea offers some of the world's best diving, with vibrant coral reefs, diverse marine life, and excellent visibility. Popular dive sites include Ras Mohammed National Park near Sharm El Sheikh, the SS Thistlegorm wreck, the Blue Hole near Dahab, and the Brothers Islands. Diving centers throughout the Red Sea coast offer courses for beginners and guided trips for certified divers.",
            "desert_safaris": "Desert safaris by 4x4 or camel provide adventures into Egypt's vast deserts. The White Desert near Bahariya Oasis is famous for its surreal chalk formations. Siwa Oasis offers dune bashing and visits to freshwater springs. Sinai desert trips often include Bedouin dinners and stargazing. Multi-day safaris allow for camping under the stars.",
            "nile_cruises": "Cruising the Nile between Luxor and Aswan is a classic Egyptian experience, combining sightseeing with relaxation. Most cruises stop at Edfu and Kom Ombo temples. Options range from luxury cruise ships to traditional sailing feluccas. Dinner cruises in Cairo offer entertainment with views of the illuminated city.",
            "historical_tours": "Guided tours of Egypt's archaeological sites provide context and insights into ancient history. Popular options include full-day tours of the Giza Pyramids and Memphis, Valley of the Kings tours in Luxor, and Abu Simbel excursions from Aswan. Private Egyptologist guides can be arranged for more in-depth experiences.",
            "hot_air_ballooning": "Hot air balloon rides over Luxor at sunrise offer breathtaking views of the Nile, temples, and surrounding landscape. Flights typically last about 45 minutes and provide unique photo opportunities of sites like the Valley of the Kings and Hatshepsut's Temple from above.",
            "shopping": "Shopping experiences range from haggling in traditional markets like Khan El Khalili to browsing fixed-price souvenir shops and modern malls. Popular purchases include papyrus, spices, alabaster, carpets, and gold jewelry. Government-certified shops provide certificates of authenticity for antiquity replicas.",
            "cooking_classes": "Egyptian cooking classes offer hands-on experience preparing traditional dishes like koshari, molokhia, and ta'ameya. Classes often include market visits to select ingredients and explanations of culinary history and techniques. Available in major tourist cities, particularly Cairo and Luxor.",
            "sound_and_light_shows": "Sound and light shows at major archaeological sites like the Pyramids, Karnak Temple, and Philae Temple tell the history of these monuments through dramatic narration, music, and illumination. Shows are presented in multiple languages and provide an atmospheric evening activity."
        }

    @staticmethod
    def _load_faq() -> Dict[str, str]:
        return {
            "best_time_to_visit": "The best time to visit Egypt is from October to April when temperatures are milder. December and January are peak season with higher prices. Summer (June-August) is extremely hot, especially in Upper Egypt, but offers lower prices and fewer crowds at ancient sites. May and September are shoulder seasons with decent weather and fewer tourists.",
            "visa_requirements": "Most visitors need a visa for Egypt. Options include an e-visa obtained online before travel, visa on arrival at Egyptian airports (for many nationalities), or visas from Egyptian embassies abroad. Single-entry tourist visas are valid for 30 days and cost approximately $25 USD. Always check the latest requirements before traveling.",
            "is_egypt_safe": "Egypt is generally safe for tourists, with strong security presence in tourist areas. Like any destination, normal precautions should be taken regarding belongings and awareness of surroundings. Some areas, particularly North Sinai and desert borders, should be avoided. It's advisable to check your government's travel advisories before visiting.",
            "what_to_wear": "Egypt is a conservative Muslim country. In tourist areas and resorts, dress codes are relaxed, but in cities and cultural sites, modest dress is appropriate. Women should cover shoulders and knees, and men should avoid shorts in non-resort areas. At Red Sea resorts, Western-style swimwear is acceptable. Always carry a light scarf for visiting mosques.",
            "money_matters": "The Egyptian Pound (EGP) is the local currency. ATMs are widely available in cities and tourist areas. Credit cards are accepted at hotels and larger restaurants but carry cash for smaller establishments and markets. Tipping (baksheesh) is expected for most services. USD and EUR are easily exchanged but bring clean, newer bills.",
            "internet_connectivity": "WiFi is available in most hotels, cafes, and restaurants in tourist areas, though quality varies. Local SIM cards with data plans are inexpensive and can be purchased at the airport or in mobile shops (passport required). Social media and communication apps work normally in Egypt.",
            "food_safety": "Stick to bottled water and avoid ice in less touristy areas. Reputable hotels and restaurants generally have safe food preparation standards. Street food can be delicious but choose busy stalls with high turnover. Fruits that can be peeled are safer options. Carry medication for stomach issues as a precaution.",
            "transportation_options": "Between cities, domestic flights save time, while trains connect Cairo with Alexandria and Upper Egypt. Within cities, use ride-hailing apps like Uber or Careem for convenience and fixed pricing. The Cairo Metro is efficient for getting around the capital. For sightseeing, consider hiring a driver for the day or joining organized tours.",
            "language_barrier": "Arabic is the official language, but English is widely spoken in tourist areas, hotels, and restaurants. Learning a few basic Arabic phrases like 'shukran' (thank you) and 'min fadlak' (please) is appreciated. Tour guides are available in many languages, including English, French, German, Italian, Spanish, Russian, and Japanese.",
            "electricity": "Egypt uses 220V with European-style two-pin round plugs (Type C). Adapters are easily found, but bring your own to be safe. Power outages can occur, though major hotels usually have generators.",
            "photography_rules": "Photography is restricted in some locations, including many museum interiors, some tombs, and airports. Many sites charge camera fees or require special photography tickets. Always ask before photographing local people, and be respectful of religious sites. Drones are strictly regulated and generally not permitted without advance authorization."
        }
