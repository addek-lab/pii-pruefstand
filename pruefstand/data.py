"""Wortlisten für die synthetischen Dokumente.

Die Listen des Generators sind absichtlich größer als die Wortlisten der Referenz-Erkennung:
Ein Filter kennt nie alle Namen, Medikamente oder Diagnosen.
"""

FIRST_NAMES = [
    "Anna", "Lukas", "Sophie", "Jonas", "Leonie", "Felix", "Marie", "Maximilian", "Hannah", "Paul",
    "Laura", "Tim", "Lena", "Niklas", "Julia", "Jan", "Katharina", "Moritz", "Sarah", "David",
    "Mia", "Elias", "Emma", "Noah", "Lea", "Ben", "Clara", "Finn", "Johanna", "Tobias",
    "Nadine", "Stefan", "Petra", "Michael", "Sabine", "Thomas", "Andrea", "Markus", "Claudia", "Jürgen",
    "Ayşe", "Mehmet", "Fatma", "Emre", "Olga", "Dmitri", "Katarzyna", "Piotr", "Elif", "Yusuf",
]

LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
    "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun",
    "Krüger", "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner", "Krause", "Meier", "Lehmann", "Köhler",
    "Yılmaz", "Kaya", "Demir", "Çelik", "Nowak", "Kowalski", "Petrov", "Schäfer", "Vogel", "Berger",
]

STREETS = [
    "Hauptstraße", "Bahnhofstraße", "Gartenweg", "Lindenallee", "Schillerstraße", "Goethestraße",
    "Am Markt", "Kirchplatz", "Rosenweg", "Mühlenstraße", "Berliner Allee", "Ringstraße",
    "Industriestraße", "Waldweg", "Schulstraße", "Zum Alten Hof", "An der Linde",
]

CITIES = [
    ("Berlin", "10115"), ("Hamburg", "20095"), ("München", "80331"), ("Köln", "50667"),
    ("Frankfurt am Main", "60311"), ("Stuttgart", "70173"), ("Leipzig", "04109"), ("Dresden", "01067"),
    ("Hannover", "30159"), ("Nürnberg", "90402"), ("Bremen", "28195"), ("Essen", "45127"),
    ("Dortmund", "44135"), ("Mannheim", "68159"), ("Kassel", "34117"),
]

DIAGNOSES = [
    ("E11.9", "Diabetes mellitus Typ 2"), ("I10", "arterielle Hypertonie"), ("J45.0", "allergisches Asthma"),
    ("F32.1", "mittelgradige depressive Episode"), ("M54.5", "Kreuzschmerz"), ("K29.7", "Gastritis"),
    ("N39.0", "Harnwegsinfekt"), ("C50.9", "Mammakarzinom"), ("E78.0", "Hypercholesterinämie"),
    ("G43.9", "Migräne"), ("F41.1", "generalisierte Angststörung"), ("I48.0", "Vorhofflimmern"),
]

MEDICATIONS = [
    "Metformin", "Ramipril", "Ibuprofen", "Salbutamol", "Sertralin", "Pantoprazol",
    "Amoxicillin", "Atorvastatin", "Levothyroxin", "Sumatriptan",
]

EMPLOYERS_NOISE = ["Stadtwerke", "Logistik GmbH", "Bäckerei Sonnenschein", "IT-Systemhaus", "Pflegedienst Nord"]

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]

# Was die Referenz-Erkennung "kennt" (bewusst nur ein Teil):
GAZETTEER_FIRST_NAMES = FIRST_NAMES[:30]
GAZETTEER_MEDICATIONS = MEDICATIONS[:6]
GAZETTEER_DIAGNOSES = [d[1] for d in DIAGNOSES[:8]]

# Risikostufen für die Auswertung (Orientierung, keine Rechtsberatung)
CRITICAL = {"IBAN", "KREDITKARTE", "STEUER_ID", "KVNR", "ICD10", "DIAGNOSE", "MEDIKAMENT"}
LABEL_DE = {
    "PERSON": "Person (Name)", "ADRESSE": "Straße + Hausnr.", "PLZ_ORT": "PLZ + Ort",
    "GEBURTSDATUM": "Geburtsdatum", "TELEFON": "Telefon", "EMAIL": "E-Mail",
    "IBAN": "IBAN", "BIC": "BIC", "KREDITKARTE": "Kreditkarte", "STEUER_ID": "Steuer-ID",
    "KVNR": "Krankenversichertennr.", "ICD10": "ICD-10-Code", "DIAGNOSE": "Diagnose (Text)",
    "MEDIKAMENT": "Medikament",
}
ALL_LABELS = list(LABEL_DE)
