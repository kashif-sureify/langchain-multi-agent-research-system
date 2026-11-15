"""
Topic categories for the "Explore ideas by category" picker.

To add a category, add one Category to CATEGORIES. The UI shows it as a new button,
and the model uses its focus to suggest research topics for it. Nothing else needs to change.

This file is plain data with no model imports, so the UI can load it even before the backend is set up.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    name: str  # shown on the button, and sent to the model
    icon: str  # Material Symbols icon name (fonts.google.com/icons), shown before the name
    focus: str  # tells the model what belongs in this category
    examples: tuple[str, ...]  # saved topics: the starter mix on page load, and the fallback if the model fails

    @property
    def label(self) -> str:
        return f":material/{self.icon}: {self.name}"


CATEGORIES = [
    Category(
        name="AI & Technology",
        icon="memory",
        focus="artificial intelligence, software, computing hardware, cybersecurity, robotics and consumer tech",
        examples=(
            "How AI agents are changing software development",
            "Small language models in 2026",
            "Latest breakthroughs in quantum computing",
            "Post-quantum cryptography: who is migrating and why",
        ),
    ),
    Category(
        name="Space",
        icon="rocket_launch",
        focus="space exploration, missions, astronomy, astrophysics, satellites and the space industry",
        examples=(
            "NASA's Artemis program and the return to the Moon",
            "Latest discoveries from the James Webb Space Telescope",
            "How reusable rockets are cutting the cost of reaching orbit",
            "The search for life on Mars and icy moons",
        ),
    ),
    Category(
        name="Science",
        icon="science",
        focus="physics, chemistry, biology, materials science, mathematics and major research discoveries",
        examples=(
            "Progress toward commercial nuclear fusion",
            "How AlphaFold changed protein research",
            "Room-temperature superconductors: claims and evidence",
            "New materials for faster, more efficient computer chips",
        ),
    ),
    Category(
        name="Health & Medicine",
        icon="monitor_heart",
        focus="medicine, public health, drug development, mental health, nutrition and medical technology",
        examples=(
            "CRISPR gene therapy: recent clinical results",
            "GLP-1 drugs beyond weight loss",
            "mRNA vaccines for cancer",
            "Brain-computer interfaces in clinical trials",
        ),
    ),
    Category(
        name="Climate & Environment",
        icon="eco",
        focus="climate change, energy, conservation, pollution, biodiversity and sustainability",
        examples=(
            "Solid-state batteries for electric vehicles",
            "Direct air capture of carbon dioxide",
            "Microplastics and human health",
            "Coral reef bleaching and restoration efforts",
        ),
    ),
    Category(
        name="Art & Culture",
        icon="palette",
        focus="visual art, literature, architecture, museums, music, film and cultural heritage",
        examples=(
            "How generative AI is changing the art world",
            "Museums returning looted artifacts to their countries of origin",
            "Why vinyl records made a comeback",
            "How streaming changed the economics of music",
        ),
    ),
    Category(
        name="History",
        icon="history_edu",
        focus="historical events, archaeology, ancient civilizations and new discoveries about the past",
        examples=(
            "Recent archaeological discoveries in Egypt",
            "How ancient DNA is rewriting the history of human migration",
            "Reading the Herculaneum scrolls with AI",
            "What caused the Late Bronze Age collapse",
        ),
    ),
    Category(
        name="Business & Economy",
        icon="work",
        focus="markets, companies, startups, trade, jobs, personal finance and economic policy",
        examples=(
            "The four-day work week: results from trials",
            "How tariffs are reshaping global supply chains",
            "Central bank digital currencies around the world",
            "The rise of the creator economy",
        ),
    ),
    Category(
        name="Sports",
        icon="emoji_events",
        focus="professional and amateur sports, major tournaments, athletes, sports science and the business of sport",
        examples=(
            "How data analytics changed professional football",
            "The sports science behind marathon world records",
            "The growth of women's football",
            "Esports: is it becoming a mainstream sport?",
        ),
    ),
    Category(
        name="Society & Politics",
        icon="groups",
        focus="elections, government policy, law, education, cities, migration and social trends",
        examples=(
            "How AI is changing classroom education",
            "Countries regulating social media for teenagers",
            "Universal basic income experiments and their results",
            "Remote work and the future of city centers",
        ),
    ),
    Category(
        name="Food & Agriculture",
        icon="potted_plant",
        focus="food, cooking, farming, food security and the future of what we eat",
        examples=(
            "Lab-grown meat: regulation and market progress",
            "Vertical farming at commercial scale",
            "How climate change is affecting coffee and cocoa crops",
            "The science of ultra-processed foods",
        ),
    ),
]

CATEGORY_BY_NAME = {category.name: category for category in CATEGORIES}
