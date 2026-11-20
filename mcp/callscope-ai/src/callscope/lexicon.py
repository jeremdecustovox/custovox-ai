"""Small bilingual (FR/EN) lexicons. Deliberately simple and inspectable."""

POSITIVE = {
    "merci", "parfait", "super", "génial", "excellent", "content", "satisfait", "ravi", "bien", "top",
    "thanks", "thank", "great", "perfect", "happy", "excellent", "good", "appreciate",
}
NEGATIVE = {
    "inadmissible", "scandaleux", "nul", "énervé", "enervé", "marre", "problème", "probleme", "panne", "arnaque",
    "inacceptable", "déçu", "decu", "plainte", "honteux", "catastrophe", "impossible", "attends",
    "terrible", "angry", "unacceptable", "ridiculous", "broken", "worst", "furious", "disappointed", "complaint",
}
NEGATORS = {"pas", "jamais", "ne", "not", "never", "no"}

REASONS = {
    "billing": ["facture", "facturation", "prélèvement", "prelevement", "remboursement", "tarif", "invoice", "bill", "refund", "charged"],
    "cancellation": ["résilier", "resilier", "résiliation", "resiliation", "annuler", "cancel", "unsubscribe", "close my account"],
    "outage": ["panne", "coupure", "plus de connexion", "ne marche plus", "ne fonctionne plus", "outage", "not working", "down"],
    "delivery": ["livraison", "colis", "commande", "delivery", "parcel", "order"],
    "technical_support": ["bug", "erreur", "installer", "configurer", "mot de passe", "password", "error", "install"],
    "subscription_change": ["changer d'offre", "forfait", "abonnement", "upgrade", "downgrade", "plan"],
}

MOMENTS = {
    "complaint": ["inadmissible", "scandaleux", "plainte", "inacceptable", "honteux", "complaint", "unacceptable", "ridiculous"],
    "churn_threat": ["résilier", "resilier", "changer d'opérateur", "changer d'operateur", "je pars", "concurrent", "cancel my", "switch to", "leave you"],
    "agent_promise": ["je vous rappelle", "je m'engage", "je vous promets", "avant demain", "sous 48", "i will call you back", "i promise", "within 48"],
}
