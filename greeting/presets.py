"""Occasion presets for messages and background prompts."""

OCCASIONS: dict[str, dict[str, str]] = {
    "Christmas": {
        "message": "Merry Christmas",
        "subtitle": "Wishing you joy and peace",
        "prompt": (
            "Premium luxury Christmas greeting card background, sophisticated editorial "
            "holiday styling, deep evergreen and warm champagne-gold palette, elegant "
            "fir branches and subtle pinecones framing the outer edges, delicate warm "
            "fairy lights creating soft golden bokeh, gentle snowfall in the background, "
            "a beautifully illuminated Christmas tree softly visible in the distance, "
            "rich cinematic depth, refined textures, soft atmospheric glow, balanced "
            "symmetrical composition, large clean negative space in the center reserved "
            "for greeting typography, luxurious printed-card aesthetic, photorealistic, "
            "high detail, elegant and timeless, no people, no text, no letters, no numbers."
        ),
    },

    "New Year": {
        "message": "Happy New Year",
        "subtitle": "Cheers to a bright beginning",
        "prompt": (
            "Luxury New Year greeting card background, sophisticated midnight-blue and "
            "deep navy atmosphere with elegant champagne-gold accents, graceful golden "
            "fireworks concentrated around the upper corners and distant horizon, subtle "
            "sparkling particles and refined bokeh, faint city lights far in the background, "
            "cinematic depth and premium editorial lighting, sophisticated festive mood, "
            "wide uncluttered negative space through the center for typography, visually "
            "balanced composition, luxurious paper-and-print aesthetic, high detail, "
            "polished and elegant, no people, no text, no letters, no numbers."
        ),
    },

    "Birthday": {
        "message": "Happy Birthday",
        "subtitle": "Hope your day is wonderful",
        "prompt": (
            "Premium elegant birthday greeting card background, sophisticated plum, "
            "burgundy and champagne-gold color palette, tasteful balloons and delicate "
            "confetti framing the outer edges rather than filling the center, subtle "
            "floating golden particles, soft studio lighting, gentle luminous glow, "
            "beautiful layered depth, refined celebration atmosphere, modern luxury "
            "stationery aesthetic, generous clean negative space in the center for "
            "greeting typography, balanced composition, photorealistic details, "
            "high-end printed greeting card, no people, no text, no letters, no numbers."
        ),
    },

    "Eid": {
        "message": "Eid Mubarak",
        "subtitle": "Peace and blessings to you",
        "prompt": (
            "Luxury Eid greeting card background, deep emerald green, midnight teal "
            "and warm antique gold palette, elegant crescent moon positioned toward an "
            "upper corner, delicate ornate lanterns and refined Islamic geometric motifs "
            "framing the edges, subtle golden illumination, soft atmospheric particles, "
            "rich velvet-like depth, sophisticated cultural elegance, peaceful and "
            "celebratory mood, beautifully controlled lighting, large uncluttered center "
            "area reserved for greeting typography, premium stationery aesthetic, "
            "high detail, no people, no text, no calligraphy, no letters, no numbers."
        ),
    },

    "Diwali": {
        "message": "Happy Diwali",
        "subtitle": "May your home be full of light",
        "prompt": (
            "Premium Diwali greeting card background, deep indigo and royal blue night "
            "atmosphere with rich saffron, amber and antique-gold highlights, elegant "
            "traditional diyas arranged subtly along the lower and side edges, delicate "
            "golden sparkles and soft floating light particles, refined ornamental details "
            "in the corners, warm radiant glow spreading gently toward the center, "
            "luxurious festive atmosphere, sophisticated Indian-inspired decorative "
            "aesthetic, generous clean negative space in the center for typography, "
            "cinematic lighting, high detail, elegant printed-card finish, no people, "
            "no text, no letters, no numbers."
        ),
    },

    "Hanukkah": {
        "message": "Happy Hanukkah",
        "subtitle": "Wishing you light and warmth",
        "prompt": (
            "Elegant premium Hanukkah greeting card background, rich midnight blue and "
            "soft silver palette with subtle warm candlelight, tasteful menorah-inspired "
            "candle glow placed near the edges, delicate silver stars and refined bokeh, "
            "soft luminous atmosphere, sophisticated layered depth, peaceful and welcoming "
            "mood, modern luxury stationery design, beautifully balanced composition, "
            "large clean negative space in the center reserved for greeting typography, "
            "high-end printed card aesthetic, no people, no text, no letters, no numbers."
        ),
    },

    "Halloween": {
        "message": "Happy Halloween",
        "subtitle": "Have a fun and spooky night",
        "prompt": (
            "Stylish premium Halloween greeting card background, deep violet and "
            "charcoal-purple night sky, glowing warm orange moon positioned toward an "
            "upper corner, subtle silhouettes of bats around the outer edges, faint "
            "mist and atmospheric particles, elegant autumn branches framing the scene, "
            "soft amber highlights, mysterious but tasteful mood, cinematic lighting, "
            "rich depth, sophisticated editorial Halloween aesthetic, large uncluttered "
            "negative space in the center for typography, high-detail premium card finish, "
            "no people, no text, no letters, no numbers."
        ),
    },

    "Thanksgiving": {
        "message": "Happy Thanksgiving",
        "subtitle": "Grateful for you",
        "prompt": (
            "Luxury Thanksgiving greeting card background, warm amber, burnt sienna, "
            "chestnut brown and muted cream palette, elegant autumn leaves naturally "
            "framing the corners and lower edges, subtle acorns and delicate seasonal "
            "botanical details, warm diffused sunlight, soft golden glow, rich organic "
            "textures, sophisticated cozy atmosphere, cinematic depth, premium editorial "
            "stationery aesthetic, spacious uncluttered center reserved for greeting "
            "typography, beautifully balanced composition, high detail, no people, "
            "no text, no letters, no numbers."
        ),
    },

    "Valentine's Day": {
        "message": "Happy Valentine's Day",
        "subtitle": "With love",
        "prompt": (
            "Elegant luxury Valentine's Day greeting card background, sophisticated "
            "burgundy, deep rose, dusty pink and champagne palette, delicate translucent "
            "hearts subtly framing the corners, soft rose petals near the lower edges, "
            "warm romantic glow, gentle diffused light, refined bokeh, luxurious velvet "
            "and paper-like visual texture, tasteful romantic atmosphere without being "
            "overly busy, generous clean negative space in the center for typography, "
            "premium editorial greeting-card design, cinematic depth, high detail, "
            "no people, no text, no letters, no numbers."
        ),
    },

    "Easter": {
        "message": "Happy Easter",
        "subtitle": "Hope and new beginnings",
        "prompt": (
            "Premium elegant Easter greeting card background, airy spring atmosphere, "
            "soft sage green, pale cream, blush and warm champagne palette, delicate "
            "spring blossoms and fresh botanical branches framing the edges, subtle "
            "pastel eggs naturally integrated into the surrounding composition, gentle "
            "morning sunlight, soft luminous bokeh, fresh and uplifting mood, refined "
            "editorial stationery aesthetic, bright spacious center reserved for greeting "
            "typography, elegant depth and realistic botanical detail, high-end printed "
            "card finish, no people, no text, no letters, no numbers."
        ),
    },

    "Wedding": {
        "message": "Congratulations",
        "subtitle": "Wishing you a beautiful life together",
        "prompt": (
            "Luxury wedding greeting card background, sophisticated ivory, champagne, "
            "deep burgundy and muted gold palette, elegant delicate floral arrangements "
            "framing the upper corners and lower edges, subtle fine-art botanical details, "
            "soft romantic candlelight, creamy luminous center, refined gold accents, "
            "beautiful depth of field, timeless editorial wedding stationery aesthetic, "
            "quietly luxurious and sophisticated, large pristine negative space in the "
            "center reserved for typography, high-end print quality, photorealistic "
            "textures, no people, no text, no letters, no numbers."
        ),
    },

    "Graduation": {
        "message": "Congratulations Graduate",
        "subtitle": "So proud of you",
        "prompt": (
            "Premium graduation greeting card background, sophisticated navy, midnight "
            "blue and champagne-gold palette, elegant academic-inspired atmosphere, "
            "subtle graduation cap silhouette and refined gold confetti concentrated "
            "near the outer edges, soft celebratory light, gentle golden particles, "
            "cinematic depth, modern prestigious editorial design, dignified and inspiring "
            "mood, large uncluttered center reserved for greeting typography, premium "
            "stationery and luxury print aesthetic, crisp high detail, no people, "
            "no text, no letters, no numbers."
        ),
    },

    "Thank You": {
        "message": "Thank You",
        "subtitle": "Your kindness means a lot",
        "prompt": (
            "Elegant luxury thank-you greeting card background, sophisticated sage green, "
            "warm ivory, soft champagne and muted botanical tones, delicate hand-crafted "
            "botanical sprigs framing the corners, subtle leaves and tiny blossoms, soft "
            "natural daylight, gentle creamy glow, refined paper texture, peaceful and "
            "graceful atmosphere, minimalist editorial stationery aesthetic, beautiful "
            "layered depth without clutter, generous clean negative space in the center "
            "reserved for greeting typography, premium printed-card appearance, high detail, "
            "no people, no text, no letters, no numbers."
        ),
    },
}

PROJECT_CAPTION = (
    "Just completed my Seasonal Greeting Image Tool Agent! "
    "Generate, customize, and share festive greetings with AI—quick and easy! "
    "#rehancodingwithai #codingwithai"
)


def occasion_names() -> list[str]:
    return list(OCCASIONS.keys())
