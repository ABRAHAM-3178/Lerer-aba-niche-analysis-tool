"""
常量定义 - 词库、停用词、品牌词等
"""

CATEGORY_KEYWORDS = {
    "电子": ["phone", "headphone", "speaker", "charger", "cable", "adapter", "battery", "earbud", "microphone", "camera", "drone", "tablet", "laptop", "keyboard", "mouse", "monitor"],
    "家居": ["chair", "table", "lamp", "rug", "curtain", "blanket", "pillow", "mattress", "shelf", "organizer", "basket", "pot", "pan", "knife", "cutting", "board"],
    "服饰": ["shirt", "pants", "jeans", "jacket", "coat", "sweater", "hoodie", "dress", "skirt", "shorts", "socks", "shoes", "boots", "hat", "cap", "belt", "bag", "backpack"],
    "美妆": ["cream", "lotion", "serum", "oil", "mask", "scrub", "wash", "shampoo", "conditioner", "soap", "sunscreen", "foundation", "lipstick", "mascara", "eyeliner"],
    "运动": ["mat", "ball", "glove", "strap", "band", "belt", "towel", "bottle", "shoes", "sneaker", "cycle", "bike", "yoga", "fitness", "dumbbell", "resistance"],
    "母婴": ["diaper", "wipe", "bottle", "stroller", "carrier", "crib", "baby", "toddler", "toy", "book", "puzzle", "rattle", "teether"],
    "办公": ["pen", "pencil", "notebook", "folder", "binder", "tape", "glue", "scissor", "ruler", "stapler", "marker", "paper", "sticker", "label", "desk"],
    "工具": ["drill", "saw", "hammer", "screwdriver", "wrench", "level", "measure", "knife", "flashlight", "pliers", "socket"],
    "宠物": ["food", "toy", "leash", "collar", "bed", "bowl", "litter", "treat", "chew", "brush", "shampoo", "carrier", "crate"],
    "汽车": ["charger", "mat", "cover", "cleaner", "polish", "holder", "mount", "tool", "organizer", "light", "wiper"],
    "食品": ["snack", "candy", "chocolate", "cookie", "chip", "nut", "tea", "coffee", "spice", "oil", "sauce", "seasoning"],
    "图书": ["book", "guide", "manual", "workbook", "journal", "planner", "notebook", "dictionary", "encyclopedia", "textbook"],
    "玩具": ["lego", "doll", "action", "figure", "board", "game", "puzzle", "car", "train", "block", "stuffed", "plush"],
}

GENERIC_BASE_WORDS = {
    "product", "item", "set", "kit", "pack", "box", "case", "bag", "holder",
    "stand", "mount", "cover", "strap", "belt", "clip", "hook", "tool",
    "accessory", "supply", "material", "equipment"
}

STOP_WORDS = {
    'for', 'with', 'without', 'and', 'or', 'the', 'a', 'an', 'to', 'from',
    'on', 'at', 'in', 'by', 'of', 'for', 'on', 'at', 'to', 'in', 'by',
    'with', 'without', 'plus', 'extra', 'new', 'best', 'top', 'high',
    'quality', 'premium', 'deluxe', 'pro', 'max', 'mini', 'plus', 'super',
    'ultra', 'extreme', 'ultimate', 'perfect', 'great', 'excellent', 'amazing',
    'awesome', 'fantastic', 'wonderful', 'terrific', 'marvelous', 'exceptional',
    'outstanding', 'superb', 'fabulous', 'incredible', 'unbelievable'
}

BRAND_SUFFIXES = {
    'amazon', 'echo', 'kindle', 'fire', 'ring', 'blink', 'eero',
    'apple', 'iphone', 'ipad', 'airpods', 'macbook', 'watch', 'imac',
    'samsung', 'galaxy', 'note', 'fold', 'buds', 'tab',
    'sony', 'playstation', 'wh', 'wf', 'xperia', 'bravia',
    'anker', 'soundcore', 'eufy', 'nebula',
    'jbl', 'charge', 'flip', 'tune', 'go',
    'bose', 'qc', 'soundlink', 'sport',
    'sonos', 'roam', 'move', 'era',
    'dyson', 'roomba', 'shark',
    'instant', 'pot', 'ninja', 'kitchenaid', 'vitamix', 'breville',
    'philips', 'sonicare', 'hue',
    'nintendo', 'switch', 'playstation', 'xbox',
    'lego', 'mattel', 'hasbro', 'crayola',
    'microsoft', 'surface', 'google', 'pixel', 'huawei', 'xiaomi'
}

BRAND_PATTERNS = [
    r'for\s+(amazon|echo|kindle|fire|ring|blink)',
    r'for\s+(iphone|ipad|airpods|macbook|apple|watch)',
    r'for\s+(galaxy|note|buds|watch|samsung)\s',
    r'(anker|soundcore|eufy|aukey|ravpower)',
    r'(jbl|bose|sonos|sony|philips)',
    r'(dyson|shark|roomba|braava)',
    r'(instant\s+pot|ninja|kitchenaid|vitamix|breville)',
    r'(nintendo|playstation|xbox|microsoft|google|huawei|xiaomi)',
]

MODIFIER_CATEGORIES = {
    "降噪": ["noise cancelling", "noise canceling", "anc", "active noise", "降噪", "静音", "quiet"],
    "防水": ["waterproof", "water proof", "water resistant", "splash proof", "ipx", "防水", "防泼水"],
    "快充": ["fast charge", "quick charge", "rapid charge", "pd charger", "快充", "闪充"],
    "无线": ["wireless", "bluetooth", "cordless", "真无线", "无线", "蓝牙"],
    "便携": ["portable", "compact", "mini", "travel", "便携", "迷你", "轻便", "折叠"],
    "大容量": ["large capacity", "high capacity", "20000mah", "10000mah", "大容量"],
    "智能": ["smart", "intelligent", "app control", "wifi", "智能", "自动", "感应"],
    "环保": ["eco friendly", "biodegradable", "recyclable", "organic", "环保", "可降解"],
    "舒适": ["comfortable", "soft", "ergonomic", "cushion", "舒适", "柔软", "人体工学"],
    "耐用": ["durable", "heavy duty", "long lasting", "sturdy", "耐用", "坚固", "抗摔", "耐磨"],
    "安全": ["safe", "secure", "child safe", "bpa free", "安全", "无毒", "防摔", "保护"],
    "多功能": ["multi function", "versatile", "all in one", "多功能", "多用", "合一"],
    "轻量": ["lightweight", "ultra light", "轻量", "超轻", "轻盈"],
    "透气": ["breathable", "mesh", "透气", "通风", "排汗"],
    "保暖": ["warm", "thermal", "insulated", "保暖", "加厚", "恒温"],
    "抗菌": ["antibacterial", "anti microbial", "抗菌", "抑菌", "防菌"],
    "防滑": ["non slip", "anti slip", "grip", "防滑", "止滑", "抓地"],
    "保湿": ["hydrating", "moisturizing", "保湿", "补水", "锁水"],
    "修复": ["repair", "restore", "修复", "修护", "再生"],
    "防晒": ["sunscreen", "uv protection", "防晒", "防紫外线", "spf"],
    "减震": ["shock absorption", "cushioning", "减震", "缓冲", "防震"],
    "精准": ["precise", "accurate", "精准", "精确", "高精度"],
    "高效": ["efficient", "high performance", "高效", "强力", "快速"],
    "简约": ["minimalist", "simple", "clean", "简约", "简洁", "极简"],
    "复古": ["vintage", "retro", "classic", "复古", "怀旧", "经典"],
    "时尚": ["stylish", "fashion", "trendy", "时尚", "潮流", "时髦"],
    "高端": ["luxury", "premium", "high end", "高端", "奢华", "尊贵"],
    "精致": ["delicate", "exquisite", "refined", "精致", "精美", "细腻"],
    "透明": ["transparent", "clear", "see through", "透明", "磨砂", "渐变"],
    "金属": ["metal", "metallic", "stainless", "金属", "合金", "钢"],
    "木质": ["wood", "wooden", "bamboo", "木质", "竹制", "实木"],
    "皮质": ["leather", "genuine", "faux", "皮质", "真皮", "pu皮"],
    "不锈钢": ["stainless steel", "steel", "不锈钢", "钢制"],
    "碳纤维": ["carbon fiber", "carbon", "碳纤维", "碳素"],
    "硅胶": ["silicone", "silica", "硅胶", "硅橡胶"],
    "玻璃": ["glass", "tempered", "钢化玻璃", "玻璃", "强化"],
    "真皮": ["genuine leather", "real leather", "真皮", "头层皮"],
    "棉": ["cotton", "pure cotton", "棉", "纯棉", "全棉"],
    "丝": ["silk", "satin", "丝", "丝绸", "缎面"],
    "户外": ["outdoor", "camping", "hiking", "户外", "露营", "徒步", "登山"],
    "旅行": ["travel", "luggage", "journey", "旅行", "出行", "旅途"],
    "办公": ["office", "work", "business", "办公", "商务", "职业"],
    "健身": ["fitness", "gym", "workout", "健身", "锻炼", "训练"],
    "家用": ["home", "household", "家庭", "家用", "居家人"],
    "车载": ["car", "vehicle", "auto", "车载", "车用", "汽车"],
    "厨房": ["kitchen", "cooking", "culinary", "厨房", "烹饪", "厨用"],
    "浴室": ["bath", "shower", "bathroom", "浴室", "淋浴", "卫浴"],
    "儿童": ["kids", "children", "baby", "儿童", "宝宝", "婴幼儿"],
    "宠物": ["pet", "dog", "cat", "宠物", "犬", "猫"],
    "男士": ["men", "male", "for men", "男士", "男款", "男性"],
    "女士": ["women", "female", "for women", "女士", "女款", "女性"],
    "中性": ["unisex", "neutral", "中性", "男女通用"],
    "老人": ["senior", "elderly", "aged", "老人", "老年", "长辈"],
    "孕妇": ["maternity", "pregnant", "pregnancy", "孕妇", "孕期"],
    "学生": ["student", "school", "college", "学生", "校园", "学业"],
}
