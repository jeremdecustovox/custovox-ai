"""Fictional calls for the demo mode. No real recording, no real person."""

from __future__ import annotations


def _seg(lines: list[str]) -> list[dict]:
    out, t = [], 0.0
    for text in lines:
        d = max(2.0, len(text) / 15)
        out.append({"start": round(t, 1), "end": round(t + d, 1), "text": text})
        t += d + 0.8
    return out


DEMO_CALLS = {
    "demo-1": ("2026-11-02T09:14:00", _seg([
        "Bonjour, vous parlez à Camille, comment puis-je vous aider ?",
        "Bonjour, j'ai un problème avec ma facture, on m'a prélevé deux fois ce mois-ci, c'est inadmissible.",
        "Je suis désolée, je vais vérifier tout de suite votre dossier.",
        "J'en ai marre, c'est la deuxième fois. Si ça continue je vais résilier et changer d'opérateur.",
        "Je comprends. Je m'engage à vous rembourser, et je vous rappelle avant demain pour confirmer.",
        "D'accord, merci.",
    ])),
    "demo-2": ("2026-11-03T14:02:00", _seg([
        "Bonjour, service client, comment puis-je vous aider ?",
        "Bonjour, je n'ai plus de connexion depuis ce matin, internet ne marche plus du tout.",
        "Je vais regarder, il y a une panne dans votre secteur, l'intervention est prévue cet après-midi.",
        "Ah d'accord, merci pour l'information, c'est parfait.",
    ])),
    "demo-3": ("2026-11-05T10:40:00", _seg([
        "Hello, you're speaking with Sam, how can I help?",
        "Hi, my parcel was supposed to arrive last week and the order still shows as shipped.",
        "Let me check. The delivery was delayed at the depot, it will arrive tomorrow.",
        "This is ridiculous, I paid for express delivery. I want a refund of the shipping.",
        "I understand. I promise the shipping fee will be refunded within 48 hours.",
        "Okay, thanks.",
    ])),
    "demo-4": ("2026-11-09T16:25:00", _seg([
        "Bonjour, vous parlez à Inès, comment puis-je vous aider ?",
        "Bonjour, je voudrais changer d'offre pour un forfait moins cher.",
        "Je vais regarder les offres disponibles pour vous.",
        "Super, merci beaucoup, c'est très bien.",
    ])),
    "demo-5": ("2026-11-12T11:08:00", _seg([
        "Bonjour, service client, comment puis-je vous aider ?",
        "Je veux résilier mon abonnement, le service est nul et je pars chez un concurrent.",
        "Je suis désolé de l'apprendre. Je vais noter votre demande de résiliation.",
        "C'est scandaleux, trois pannes en un mois.",
    ])),
    "demo-6": ("2026-11-16T08:50:00", _seg([
        "Hello, how can I help?",
        "I can't install the app, I get an error when I enter my password.",
        "Let me check your account. I've reset it, please try again now.",
        "It works, great, thank you.",
    ])),
}
