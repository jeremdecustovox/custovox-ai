"""Small bilingual (FR/EN) lexicons. Deliberately simple and inspectable."""

POSITIVE = {
    "merci", "parfait", "super", "génial", "excellent", "content", "satisfait", "ravi", "bien", "top",
    "thanks", "thank", "great", "perfect", "happy", "excellent", "good", "appreciate",
    # reviews
    "agréable", "agreable", "adorable", "chaleureux", "chaleureuse", "propre", "impeccable", "délicieux", "delicieux",
    "recommande", "friendly", "clean", "lovely", "delicious", "recommend", "helpful",
}
NEGATIVE = {
    "inadmissible", "scandaleux", "nul", "énervé", "enervé", "marre", "problème", "probleme", "panne", "arnaque",
    "inacceptable", "déçu", "decu", "plainte", "honteux", "catastrophe", "impossible", "attends",
    "terrible", "angry", "unacceptable", "ridiculous", "broken", "worst", "furious", "disappointed", "complaint",
    # reviews
    "saleté", "salete", "crasseux", "crasseuse", "déçue", "decue", "décevant", "decevant", "horrible", "impoli", "impolie", "mauvais", "mauvaise",
    "dirty", "rude", "awful", "overpriced", "bad",
}
NEGATORS = {"pas", "jamais", "ne", "not", "never", "no"}

REASONS = {
    "billing": ["facture", "facturation", "prélèvement", "prelevement", "remboursement", "tarif", "invoice", "bill", "refund", "charged"],
    "cancellation": ["résilier", "resilier", "résiliation", "resiliation", "annuler", "cancel", "unsubscribe", "close my account"],
    "outage": ["panne", "coupure", "plus de connexion", "ne marche plus", "ne fonctionne plus", "outage", "not working", "down"],
    "delivery": ["livraison", "colis", "commande", "delivery", "parcel", "order"],
    "technical_support": ["bug", "erreur", "installer", "configurer", "mot de passe", "password", "error", "install"],
    "subscription_change": ["changer d'offre", "forfait", "abonnement", "upgrade", "downgrade", "plan"],
    # reviews (hotels, shops, restaurants)
    "price": ["prix", "cher", "chère", "trop cher", "hors de prix", "price", "expensive", "overpriced", "pricey"],
    "product_quality": ["qualité", "qualite", "abîmé", "abîmée", "abime", "abimee", "défectueux", "défectueuse", "defectueux", "cassé", "cassée", "casse",
                        "quality", "damaged", "defective", "faulty"],
    "staff": ["personnel", "accueil", "vendeur", "vendeuse", "serveur", "serveuse", "réception", "reception",
              "réceptionniste", "staff", "employee", "waiter", "waitress", "receptionist"],
    "cleanliness": ["propreté", "proprete", "saleté", "salete", "crasseux", "crasseuse", "pas propre", "propre", "ménage", "menage", "taches",
                    "cleanliness", "dirty", "clean", "stains", "housekeeping"],
    "waiting_time": ["attente", "attendre", "file d'attente", "retard", "trop long", "lent",
                     "wait time", "waited", "waiting", "delay", "slow", "queue"],
}

MOMENTS = {
    "complaint": ["inadmissible", "scandaleux", "plainte", "inacceptable", "honteux", "complaint", "unacceptable", "ridiculous"],
    "churn_threat": ["résilier", "resilier", "changer d'opérateur", "changer d'operateur", "je pars", "concurrent", "cancel my", "switch to", "leave you",
                     "je ne reviendrai", "plus jamais", "never again", "won't be back", "won't come back"],
    "agent_promise": ["je vous rappelle", "je m'engage", "je vous promets", "avant demain", "sous 48", "i will call you back", "i promise", "within 48"],
}
