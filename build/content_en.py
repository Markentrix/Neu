# -*- coding: utf-8 -*-
"""English content of the website. Mirrors content.py: same keys, same structure.

Legal terms that insurers use under German law are given with the German word in brackets,
for example "diminished value (merkantile Wertminderung)".

Links inside text: [[en/services/valuation-report|valuation report]] (slug without leading or trailing slash).
"""

BIZ_EN = {
    "legal_name": "PS Schneider – Vehicle Engineering Expert",
    "role": "Vehicle engineering expert",
    "craft": "Master motor vehicle technician",
}

# Static pages: key -> English slug (German slugs are in build.py)
SLUGS_EN = {
    "home": "en",
    "services": "en/services",
    "guide": "en/guide",
    "why": "en/why-an-expert-report",
    "checklist": "en/accident-checklist",
    "contact": "en/contact",
    "area": "en/service-area",
    "legal": "en/legal-notice",
    "privacy": "en/privacy",
}

SERVICES = [
    {
        "slug": "en/services/liability-damage-report",
        "key": "haftpflicht",
        "short": "Liability damage report",
        "tag": "Accident damage",
        "icon": "car",
        "title": "Liability Damage Report Celle | PS Schneider",
        "desc": "Liability damage report after a not-at-fault accident in Celle: independent vehicle expert, costs usually paid by the other party's insurer.",
        "h1": "Liability damage report in Celle",
        "lede": "After a not-at-fault accident I document all damage, quantify your claims and provide the report you need when dealing with the other party's insurer.",
        "card": "After a not-at-fault accident: all damage documented, including repair time and diminished value. For a total loss with residual and replacement value. The costs are usually paid by the other party's insurer.",
        "sections": [
            {"h2": "When a liability damage report makes sense", "body": [
                "If your vehicle was damaged in an accident caused by someone else, your claims are directed against the liability insurer of the person at fault. To have these claims quantified fully and transparently, you need more than a repair estimate.",
                "An independent report is especially important if the damage goes beyond a minor scratch, if a total loss is likely, if liability is disputed or if the other insurer wants to cut your claim.",
            ]},
            {"h2": "What the report contains", "body": [
                ("ul", [
                    "All damage, documented in writing and with photos",
                    "The expected repair costs",
                    "The estimated repair time and therefore the downtime",
                    "The expected diminished value (merkantile Wertminderung)",
                    "For a total loss: residual value and replacement value (Restwert and Wiederbeschaffungswert)",
                    "Notes on previous and old damage",
                ]),
                "This gives you a reliable basis for your decision: have the car repaired, settle on the basis of the report without repairing (fiktive Abrechnung) or sell the vehicle. The report also gives you legal protection.",
            ]},
            {"h2": "How it works", "body": [
                ("ol", [
                    "You call or write to me. We briefly clarify what happened.",
                    "I inspect your vehicle by appointment and record all damage.",
                    "I prepare the report promptly so that the wait for the repair or a replacement car stays short.",
                    "You submit the report to the other party's insurer or pass it on to your lawyer.",
                ]),
            ]},
            {"h2": "Who pays for the report?", "body": [
                "In a liability case the costs of the report count as part of the damage. As a rule the insurer of the person at fault pays them. You have the right to choose the expert yourself. Insurers like to point to a repair estimate and claim that you would have to pay for an expert yourself. In a liability case that is generally not the case.",
                ("callout", "For minor damage, in case law usually up to about €750 to €1,000, a report is often not worth it. I will tell you that honestly before you place an order."),
            ]},
        ],
        "faq": [
            ("Do I have to accept the other insurer's expert?",
             "No. As the injured party you may commission an independent expert of your choice. An expert appointed by the insurer works on the insurer's behalf."),
            ("Can I have the damage paid out without repairing?",
             "Yes. This notional settlement (fiktive Abrechnung) is common for minor damage, older vehicles or if you repair the car yourself. The report also quantifies the diminished value, which can matter when you later sell the car."),
            ("What happens in the case of a total loss?",
             "Then I determine the residual value and the replacement value. On that basis you decide whether a repair is worthwhile or whether selling is the better option."),
            ("How quickly will I receive the report?",
             "I arrange the inspection at short notice and prepare the report promptly so that the wait until the repair or a replacement vehicle stays as short as possible."),
        ],
        "related": ["en/services/residual-value", "en/guide/diminished-value-after-accident", "en/guide/rental-car-loss-of-use"],
    },
    {
        "slug": "en/services/evidence-report",
        "key": "beweis",
        "short": "Evidence report",
        "tag": "Used cars and workshops",
        "icon": "search",
        "title": "Vehicle Evidence Report Celle | PS Schneider",
        "desc": "Evidence report in Celle: have hidden previous damage, faulty repairs or disputes with a workshop or seller documented neutrally.",
        "h1": "Evidence report for vehicles in Celle",
        "lede": "Something is wrong after buying a used car or after a repair? I record the condition of your vehicle neutrally so that you are protected against the seller or workshop.",
        "card": "Does the car pull to the left, or are the panel gaps uneven? Hidden previous damage and faulty repairs are recorded neutrally so you are covered against the seller or workshop.",
        "sections": [
            {"h2": "Typical situations", "body": [
                "After buying a used car or after a repair it often turns out that something is not right. Then suspicion quickly arises that previous damage was concealed or only inadequately repaired.",
                ("ul", [
                    "The vehicle pulls slightly to the left while driving",
                    "Door or panel gaps are uneven",
                    "Suspected concealed previous damage after a purchase",
                    "A repair was not carried out or was carried out poorly",
                    "A dispute with the workshop about the scope or quality of the work",
                ]),
            ]},
            {"h2": "Why you should not wait", "body": [
                "A defect is more than an annoyance. It can cause consequential damage and, in the worst case, lead to engine damage or even accidents. The earlier the condition is documented neutrally, the easier it is to prove later what was there.",
                ("callout", "Have as little as possible changed on the vehicle before it has been inspected. Keep the purchase contract, invoices and correspondence."),
            ]},
            {"h2": "What I record for you", "body": [
                ("ul", [
                    "The current condition of the vehicle, in writing and with photos",
                    "Signs of previous or old damage",
                    "Defects in repairs that were carried out",
                    "Possible consequences and risks, for example for road safety or follow-up damage",
                ]),
                "The report is neutral and can be submitted as evidence in a dispute. It gives you a solid basis for talking to the seller or workshop and for your lawyer.",
            ]},
        ],
        "faq": [
            ("Who pays for an evidence report?",
             "Unlike after a not-at-fault accident there is usually no opposing insurer who pays. You commission me directly and receive a quote in advance. Whether and to what extent the costs can later be recovered from the seller or workshop is something your lawyer will clarify in a dispute."),
            ("Can I use the report in court?",
             "A neutral report by an independent expert can be submitted as evidence in a dispute. Unlike a repair estimate, it is recognised in court."),
            ("Should I have the vehicle repaired beforehand?",
             "No. Have the condition documented first. A repair beforehand can remove traces that you later need as evidence."),
        ],
        "related": ["en/services/valuation-report", "en/services/accident-reconstruction", "en/why-an-expert-report"],
    },
    {
        "slug": "en/services/lease-return-report",
        "key": "leasing",
        "short": "Lease return report",
        "tag": "End of lease",
        "icon": "key",
        "title": "Lease Return Report Celle | PS Schneider",
        "desc": "Lease return report in Celle: independent assessment in disputes about wear and diminished value, so you do not pay excessive claims.",
        "h1": "Lease return report in Celle",
        "lede": "When a leased vehicle is returned, lessor and driver often argue about diminished value. An independent report separates normal wear from real damage.",
        "card": "Normal signs of use are not damage. An independent report protects you against excessive claims when you return a leased vehicle.",
        "sections": [
            {"h2": "Wear is not damage", "body": [
                "When leased vehicles are returned, disagreements about diminished value are common. Unfortunately there are no objective criteria that define exactly when excessive wear exists. That is why normal signs of use are often included in the assessment.",
                "Wear is not damage. Depending on the age and mileage of the vehicle it has to be accepted.",
            ]},
            {"h2": "What is normal for a used vehicle", "body": [
                ("ul", [
                    "Dents without chipped paint",
                    "Stone chips",
                    "Minor scratches on the paint or on the wheels",
                    "Light scuffs inside the car",
                ]),
                "These are generally not excessive damage that would justify a deduction in value.",
            ]},
            {"h2": "When a report helps", "body": [
                ("ul", [
                    "The lessor demands an additional payment for alleged damage after the return",
                    "You disagree with the return protocol",
                    "You want to know before the return what the lessor might object to",
                ]),
                "Bring the lease contract with the return conditions to the appointment and, if available, the return protocol. I assess the condition neutrally and record what is wear and what is damage.",
            ]},
        ],
        "faq": [
            ("When should I have the report made?",
             "Ideally before the return. Then you know what might be objected to and can decide whether a repair is worthwhile. If the claim has already arrived, the report helps afterwards too."),
            ("Do I have to repair scratches before the return?",
             "That depends on the lease contract and the condition. Have it assessed beforehand what counts as normal wear. That way you avoid repairs that are not necessary at all."),
            ("What counts as normal wear?",
             "Signs of use that fit the age and mileage, for example small scratches, stone chips, dents without chipped paint or light scuffs inside the car."),
        ],
        "related": ["en/services/valuation-report", "en/services/evidence-report", "en/why-an-expert-report"],
    },
    {
        "slug": "en/services/valuation-report",
        "key": "wert",
        "short": "Valuation report",
        "tag": "Buying, selling, classic cars",
        "icon": "tag",
        "title": "Vehicle and Classic Car Valuation Celle | PS Schneider",
        "desc": "Valuation report for cars, lorries, motorcycles, classic cars and e-bikes in Celle: the real market value of your vehicle, objectively documented.",
        "h1": "Valuation reports for vehicles in Celle",
        "lede": "A valuation report documents the real value of your vehicle. It creates transparency when buying or selling and records equipment as well as previous and old damage.",
        "card": "The real market value of your vehicle, objectively documented. Special equipment as well as previous and old damage are recorded. Ideal when buying or selling, or for your classic car.",
        "sections": [
            {"h2": "Which vehicles", "body": [
                "A valuation report determines the real value of a vehicle. That can be a car, a lorry, a commercial vehicle, a motorcycle, a classic car or even an e-bike.",
            ]},
            {"h2": "When a valuation report makes sense", "body": [
                ("ul", [
                    "When buying, to put the price of a vehicle into perspective objectively",
                    "When selling, to be able to prove the market value",
                    "For your classic car, when its value should be documented clearly",
                    "Whenever you need a neutral assessment instead of an estimate",
                ]),
                "A thorough valuation is particularly useful when buying and selling because it objectively proves the current market value of the vehicle.",
            ]},
            {"h2": "What the valuation report contains", "body": [
                ("ul", [
                    "The determined value of the vehicle",
                    "Special equipment that affects the value",
                    "Potential previous and old damage",
                    "The overall condition, documented with photos",
                ]),
                "The valuation report is an expression of transparency. It shows that there are no hidden or concealed defects and that the vehicle really corresponds to the stated price.",
                "Feel free to arrange an appointment.",
            ]},
        ],
        "faq": [
            ("What is the difference between a valuation report and a damage report?",
             "A damage report quantifies what accident damage costs and which claims follow from it. A valuation report determines, independently of any damage, what the vehicle is worth in its current condition."),
            ("Do you also prepare valuation reports for classic cars?",
             "Yes. A valuation report for your classic car is one of my services. Feel free to get in touch about your vehicle."),
            ("For which types of vehicle do you prepare valuation reports?",
             "For cars, lorries, commercial vehicles, motorcycles, classic cars and electric bicycles."),
        ],
        "related": ["en/guide/classic-car-valuation", "en/services/evidence-report", "en/services/lease-return-report"],
    },
    {
        "slug": "en/services/residual-value",
        "key": "restwert",
        "short": "Residual value assessment",
        "tag": "Total loss",
        "icon": "euro",
        "title": "Residual Value Assessment Celle | PS Schneider",
        "desc": "Residual value assessment after an accident in Celle: regional or Europe-wide, with offers, so you can decide without risk whether to repair or sell.",
        "h1": "Residual value assessment for accident vehicles in Celle",
        "lede": "What is your unrepaired vehicle still worth after the accident? I determine the residual value, obtain offers and you decide whether to repair or sell.",
        "card": "What is the unrepaired vehicle still worth? We determine the residual value regionally or Europe-wide, obtain offers and you decide without risk: repair or sell.",
        "sections": [
            {"h2": "What the residual value tells you", "body": [
                "Determining the residual value tells you what the unrepaired vehicle is still worth on the general, regional market after an accident. As a vehicle expert I document this residual value in detail in a report and can obtain different offers.",
            ]},
            {"h2": "Deciding without risk", "body": [
                "With a Europe-wide residual value assessment you decide, after the offers have been obtained, without risk whether to accept one of them. Once the residual value has been determined you have a basis for deciding whether a repair is worthwhile or whether it makes more sense to sell the vehicle.",
                ("ol", [
                    "I inspect and assess the damaged vehicle.",
                    "I document the residual value and obtain offers.",
                    "You decide: accept an offer, repair or proceed differently.",
                ]),
            ]},
            {"h2": "At-fault accident and only third-party liability cover?", "body": [
                "Did you cause the accident yourself and only have third-party liability insurance? Then I am happy to help you sell the badly damaged vehicle.",
                "After a not-at-fault accident the residual value is part of the [[en/services/liability-damage-report|liability damage report]].",
            ]},
        ],
        "faq": [
            ("What is the difference between residual value and replacement value?",
             "The replacement value (Wiederbeschaffungswert) is the amount you would have to pay for an equivalent used vehicle on the regional market. The residual value (Restwert) is the value the damaged vehicle still has in its unrepaired condition."),
            ("Do I have to accept a residual value offer?",
             "No. After the offers have been obtained, you decide whether to accept one of them."),
            ("When is it a total loss?",
             "A total loss exists when a repair is technically impossible or not economically sensible, as a rule because the repair costs exceed the replacement value."),
        ],
        "related": ["en/services/liability-damage-report", "en/guide/total-loss-residual-and-replacement-value", "en/services/valuation-report"],
    },
    {
        "slug": "en/services/accident-reconstruction",
        "key": "analyse",
        "short": "Accident reconstruction report",
        "tag": "Legal dispute",
        "icon": "chart",
        "title": "Accident Reconstruction Report Celle | PS Schneider",
        "desc": "Accident reconstruction report for legal disputes in Celle: technical reconstruction of how the accident happened, as a basis for lawyers, insurers and courts.",
        "h1": "Accident reconstruction report in Celle",
        "lede": "If how the accident happened is disputed, a technical analysis helps. I evaluate the damage pattern and traces and provide a solid basis for your lawyer, insurer and court.",
        "card": "When the course of events is disputed: technical reconstruction of the accident as a solid basis for lawyers, insurers and courts.",
        "sections": [
            {"h2": "When an accident analysis helps", "body": [
                "Disagreements are common after road accidents. The opposing insurer often also tries to deny at least part of its responsibility in order to minimise costs. When it is one person's word against another's, a technical accident analysis can clarify the facts.",
                ("ul", [
                    "Who is at fault is disputed between the parties or the insurers",
                    "There is a legal dispute in which the course of the accident has to be proven",
                    "In one party's view the damage pattern does not match the description of the accident",
                ]),
            ]},
            {"h2": "What is examined", "body": [
                "The basis is the technical facts: the damage pattern on the vehicles involved, the documented traces and the information about how the accident happened. From these I derive in a comprehensible way how the accident can have happened technically.",
                "I record the result in a report. It is neutral and suitable as a basis for your lawyer, the insurer or court proceedings.",
            ]},
            {"h2": "Initial conversation", "body": [
                "Whether and to what extent an accident analysis makes sense depends on the individual case. Call me and briefly describe the situation. Then we will clarify together what is needed and I will prepare an individual quote.",
            ]},
        ],
        "faq": [
            ("Do I need a lawyer in addition for a legal dispute?",
             "As a rule yes. The accident reconstruction report provides the technical basis. Legal representation is handled by your lawyer, with whom I work together if needed."),
            ("Is a report necessary after every accident?",
             "No. Where liability is clear, a [[en/services/liability-damage-report|liability damage report]] is usually enough. An accident analysis comes into play when the course of events is disputed."),
        ],
        "related": ["en/services/liability-damage-report", "en/services/evidence-report", "en/accident-checklist"],
    },
]

REASONS = [
    ("Free of charge for you",
     ["The costs of a vehicle expert report are usually paid by the liability insurer of the person at fault. Insurers often accept a repair estimate with photos and point out that, as the injured party, you would have to pay for an expert yourself.",
      "The law is clear on this: in a liability case you, as the injured party, have the right to commission an independent expert of your choice. The costs are counted as part of the damage and are paid by the liability insurer of the person at fault."]),
    ("More detailed costing and greater security",
     ["A report records not only the repair costs but also the possible diminished value, the expected repair time and the downtime. This serves your personal financial security.",
      "In addition, unlike a repair estimate, a neutral report is also legally recognised in court."]),
    ("Objective assessment",
     ["Several parties are usually involved in settling a claim, and each pursues its own interests. As an independent vehicle expert I assess the situation objectively and neutrally.",
      "To enforce your claims against the other party's insurer, you can submit a comprehensive report by an independent expert of your choice. That way the facts are assessed and documented objectively."]),
    ("Securing evidence",
     ["Disagreements and conflicts often arise after road accidents. The opposing insurer too often tries to deny at least part of its responsibility in order to minimise costs.",
      "With a report you are then on the safe side. Unlike a repair estimate, it is recognised in court in a dispute. It records all damage, the expected repair costs, the expected diminished value and the downtime caused by the repair."]),
    ("Notional settlement (fiktive Abrechnung)",
     ["Even if you do not have your vehicle repaired after an accident, you can have your claims for compensation paid out. Notional settlement is a common method of settling claims for minor damage, older vehicles or if you repair the damage yourself more cheaply.",
      "To assert your full claims, a report is recommended. It takes into account not only the expected repair costs but also the diminished value, which can matter when you later sell the vehicle."]),
    ("Comprehensive expertise",
     ["I worked for 17 years at the largest expert organisation in Europe. This expertise helps me record the effects of an accident in detail and document them in a meaningful report. It is always prepared competently and promptly in order to minimise waiting times.",
      "Through many different cases and continuous further training I can give you useful advice that is also valuable when dealing with lawyers and insurers."]),
]

COMPARE_ROWS = [
    ("Repair costs", True, True),
    ("Diminished value of the vehicle", False, True),
    ("Repair time and downtime", False, True),
    ("Residual value and replacement value", False, True),
    ("Previous and old damage documented", False, True),
    ("Recognised in court", False, True),
    ("Neutral, independent of workshop and insurer", False, True),
]

HOME_FAQ = [
    ("Who pays for the report?",
     "After a not-at-fault accident the costs of the report count as part of the damage. As a rule the liability insurer of the person at fault pays them. For an at-fault accident, a valuation report or an evidence report, you commission me directly and receive an individual quote in advance."),
    ("Do I have to use the expert the insurer suggests?",
     "No. As the injured party you have the right to commission an independent expert of your choice. An expert appointed by the insurer works on the insurer's behalf."),
    ("How quickly will I get my report?",
     "I arrange the inspection at short notice. The report is prepared promptly so that the wait until the repair or a replacement vehicle is as short as possible."),
    ("Can I have the damage paid out without repairing?",
     "Yes, this is called notional settlement (fiktive Abrechnung). It is common for minor damage, older vehicles or if you repair the car yourself. The report quantifies not only the repair costs but also the diminished value, which matters when you later sell the car."),
    ("What happens in the case of a total loss?",
     "Then I determine the residual value and the replacement value and, if you wish, obtain offers for the damaged vehicle. On that basis you decide whether a repair is worthwhile or whether selling is better."),
    ("Which vehicles do you prepare reports for?",
     "Cars, lorries and commercial vehicles, motorcycles, classic cars and electric bicycles."),
]

CHECKLIST = [
    ("Secure the accident scene", "Switch on the hazard lights, put on a high-visibility vest, set up the warning triangle."),
    ("Help the injured", "Give first aid."),
    ("Call the police or emergency services", "110 or 112. Answer the five Ws and wait for questions."),
    ("Exchange details with the other party", "Name, address, number plate, insurer."),
    ("Take photos and notes about what happened", "Vehicle positions, damage, surroundings. Note the contact details of witnesses."),
    ("Contact a vehicle expert", "Call us as early as possible. We will support you in settling the claim."),
]

ARTICLES = [
    {
        "slug": "en/guide/diminished-value-after-accident",
        "key": "wertminderung",
        "short": "Diminished value after an accident",
        "published": "2026-10-11", "modified": "2026-10-11",
        "title": "Diminished Value After an Accident | PS Schneider",
        "desc": "Diminished value (merkantile Wertminderung) after an accident explained: when it arises, who pays and why it should be quantified in the expert report.",
        "h1": "Diminished value after an accident: what you are entitled to",
        "lede": "Even a perfectly repaired vehicle is often worth less after an accident than before. This loss is part of your damage.",
        "summary": "Diminished value (merkantile Wertminderung) is the loss in value that remains despite a proper repair because buyers rate an accident vehicle lower. After a not-at-fault accident you can claim it from the other party's insurer on top of the repair costs. Whether it arises and how high it is depends on age, mileage and the severity of the damage. The expert report quantifies it.",
        "sections": [
            {"h2": "What is diminished value?", "body": [
                "After an accident a vehicle can usually be repaired. A stigma remains all the same: when selling, the damage has to be disclosed, and many buyers pay less for an accident vehicle. This loss in value is called merkantile Wertminderung (commercial diminished value).",
                "It must be distinguished from technical diminished value. That exists when defects actually remain after the repair, for example because a component could not be fully restored.",
            ]},
            {"h2": "When does it arise?", "body": [
                "Whether and how much a vehicle loses value depends on the individual case. Typical factors are:",
                ("ul", [
                    "The vehicle is still relatively young",
                    "The mileage is still low",
                    "The damage was considerable, for example to load-bearing or safety-relevant parts",
                    "The vehicle was accident-free before",
                ]),
                "For older vehicles with high mileage and for minor damage it is often small or does not arise at all.",
            ]},
            {"h2": "Who pays the diminished value?", "body": [
                "After a not-at-fault accident the diminished value is part of the damage. Besides the repair costs it is a separate item that you can claim from the liability insurer of the person at fault. That also applies if you do not have the car repaired and settle notionally (fiktive Abrechnung).",
            ]},
            {"h2": "Why the expert report matters", "body": [
                "A repair estimate does not contain diminished value. A vehicle expert report quantifies it in a comprehensible way, together with repair costs, repair time and, where relevant, residual value. That gives you a solid basis for your claim. More on this under [[en/services/liability-damage-report|liability damage report]].",
            ]},
        ],
        "faq": [
            ("Is diminished value also paid without a repair?",
             "Yes. You can claim diminished value for notional settlement (fiktive Abrechnung) too. It is shown separately in the report."),
            ("Is there a fixed percentage?",
             "No. The amount is determined in each individual case on the basis of vehicle age, mileage, vehicle value and extent of the damage."),
            ("Does diminished value arise for minor damage too?",
             "For minor damage and for older vehicles often not, or only slightly. I will tell you honestly beforehand whether a report is worthwhile."),
        ],
        "related": ["en/services/liability-damage-report", "en/guide/total-loss-residual-and-replacement-value", "en/guide/vehicle-report-cost"],
    },
    {
        "slug": "en/guide/total-loss-residual-and-replacement-value",
        "key": "totalschaden",
        "short": "Total loss: residual and replacement value",
        "published": "2026-10-11", "modified": "2026-10-11",
        "title": "Total Loss: Residual and Replacement Value | PS Schneider",
        "desc": "Total loss after an accident: what residual value and replacement value mean, how the compensation is calculated and when a repair is still possible.",
        "h1": "Total loss: residual value and replacement value explained",
        "lede": "In a total loss two values decide what you receive and which options you have.",
        "summary": "The replacement value (Wiederbeschaffungswert) is the price of an equivalent used vehicle. The residual value (Restwert) is the value of the damaged vehicle. If you keep or sell the vehicle yourself, the compensation as a rule results from the difference between the two values. An expert report determines both values.",
        "sections": [
            {"h2": "When is it a total loss?", "body": [
                "A total loss exists when a repair is technically no longer possible or not economically sensible. A repair is as a rule not economically sensible when the repair costs are higher than the replacement value.",
            ]},
            {"h2": "The three terms", "body": [
                ("ul", [
                    "Replacement value (Wiederbeschaffungswert): the amount you would have to pay for an equivalent used vehicle on the regional market",
                    "Residual value (Restwert): the value the damaged vehicle still has in its unrepaired condition, for example when sold to a residual value buyer",
                    "Replacement expense (Wiederbeschaffungsaufwand): replacement value minus residual value, as a rule the amount the insurer pays if you keep the vehicle or sell it yourself",
                ]),
                ("callout", "Example with assumed figures: if the replacement value is €8,000 and the residual value is €2,000, the replacement expense is €6,000."),
            ]},
            {"h2": "Repair despite a total loss?", "body": [
                "Within narrow limits a repair can still be possible if it is carried out completely and properly. As a rule of thumb a limit of about 130 per cent of the replacement value is often mentioned. Whether that applies in your case depends on the circumstances. Clarify it before the repair.",
            ]},
            {"h2": "How the residual value is determined", "body": [
                "The residual value results from offers on the market. If you wish, I obtain regional or Europe-wide offers. You then decide without risk whether to accept one. More on this under [[en/services/residual-value|residual value assessment]].",
            ]},
        ],
        "faq": [
            ("What will I be paid in a total loss?",
             "As a rule the replacement value minus the residual value, provided you keep the vehicle or dispose of it yourself. The report states the exact amounts."),
            ("Do I have to accept a residual value offer?",
             "No. You decide whether to accept an offer. Get advice beforehand on how it affects the settlement."),
            ("Who determines whether it is a total loss?",
             "The report. It states the repair costs, the replacement value and the residual value and thus forms the basis for your decision."),
        ],
        "related": ["en/services/residual-value", "en/services/liability-damage-report", "en/guide/rental-car-loss-of-use"],
    },
    {
        "slug": "en/guide/rental-car-loss-of-use",
        "key": "mietwagen",
        "short": "Rental car or loss-of-use compensation",
        "published": "2026-10-11", "modified": "2026-10-11",
        "title": "Rental Car or Loss of Use After an Accident | PS Schneider",
        "desc": "Not-at-fault accident: entitlement to a rental car or loss-of-use compensation for the repair period. What applies, who pays and the role of the report.",
        "h1": "Rental car or loss-of-use compensation after a not-at-fault accident",
        "lede": "While your vehicle is in the workshop or has to be replaced, you are as a rule entitled to compensation.",
        "summary": "After a not-at-fault accident you can either take a rental car or claim loss-of-use compensation (Nutzungsausfallentschädigung) for the duration of the repair or the replacement. The duration results from the expert report. The costs are as a rule paid by the other party's insurer.",
        "sections": [
            {"h2": "Two options", "body": [
                ("ul", [
                    "Rental car: you rent a comparable vehicle. The necessary costs are as a rule reimbursed by the insurer of the person at fault.",
                    "Loss of use: you do without a rental car and receive a flat daily compensation for every day without a vehicle, which depends on the vehicle type.",
                ]),
            ]},
            {"h2": "How long does the entitlement last?", "body": [
                "What counts is the duration of the repair or, in a total loss, the time needed to obtain a replacement vehicle. The report states the expected repair time and the downtime. It is therefore the basis for this claim.",
            ]},
            {"h2": "What to look out for", "body": [
                ("ul", [
                    "Choose a rental vehicle that corresponds to your own. A much more expensive vehicle is as a rule not fully reimbursed.",
                    "Agree the rental car and its duration with your expert or lawyer before you sign.",
                    "Order the repair promptly. The downtime should stay reasonable.",
                    "Loss-of-use compensation only applies if you would actually have used the vehicle and could not use it.",
                ]),
                ("callout", "Whether and how much you are entitled to in an individual case depends on the circumstances. If you have a dispute with the insurer, your lawyer will help."),
            ]},
        ],
        "faq": [
            ("Who pays for the rental car?",
             "After a not-at-fault accident as a rule the liability insurer of the person at fault, to the extent that the costs are necessary."),
            ("Which is better, rental car or loss of use?",
             "That depends on whether you need a car every day. If you can manage without a vehicle, people often choose the flat-rate compensation. If you drive regularly, you need the rental car."),
            ("Is the repair time stated in the report?",
             "Yes. The report states the expected repair time and the downtime. In a total loss that is the time to allow for a replacement."),
        ],
        "related": ["en/services/liability-damage-report", "en/guide/diminished-value-after-accident", "en/accident-checklist"],
    },
    {
        "slug": "en/guide/vehicle-report-cost",
        "key": "kosten",
        "short": "What does a vehicle expert report cost?",
        "published": "2026-10-11", "modified": "2026-10-11",
        "title": "What Does a Vehicle Expert Report Cost? | PS Schneider",
        "desc": "Cost of a vehicle expert report: who pays in a liability case, what the fee depends on and for which reports you receive an individual quote.",
        "h1": "What does a vehicle expert report cost and who pays for it?",
        "lede": "The most important answer first: after a not-at-fault accident you generally do not have to pay for the report yourself.",
        "summary": "In a liability case the costs of the report count as part of the damage and are paid by the insurer of the person at fault. For accident damage the fee is often based on the amount of the damage. For valuation, evidence and lease return reports you receive an individual quote in advance.",
        "sections": [
            {"h2": "After a not-at-fault accident", "body": [
                "In a liability case the costs of the report count as part of the damage incurred. As a rule the liability insurer of the person at fault pays them. You have the right to commission an independent expert of your choice.",
                "Insurers like to point to a repair estimate and claim that you would have to pay for an expert yourself. In a liability case that is generally not the case. The reasons are given under [[en/why-an-expert-report|reasons for an expert report]].",
                ("callout", "For minor damage a report is often not worth it. I will tell you that honestly before you place an order."),
            ]},
            {"h2": "After an at-fault accident", "body": [
                "If you caused the accident yourself, there is no opposing party who pays for the report. In that case you generally bear the costs yourself. Check beforehand whether your comprehensive cover insurer prescribes its own procedure.",
            ]},
            {"h2": "What the fee depends on", "body": [
                "For accident damage the fee is often based on the amount of the damage. For valuation, evidence and lease return reports it depends on the effort involved, for example on the type of vehicle and the scope of the documentation.",
            ]},
            {"h2": "How to get a quote", "body": [
                "Call me or write to me briefly about what it is about. For reports that you pay for yourself you receive an individual quote in advance. An overview of all reports can be found under [[en/services|services]].",
            ]},
        ],
        "faq": [
            ("Is a report worthwhile for minor damage?",
             "Usually not. For minor damage a repair estimate is often enough. For larger damage, a total loss or disputed liability a report is almost always worthwhile."),
            ("Does the insurer sometimes reduce the expert's costs?",
             "Reductions do happen. In that case, get advice from your lawyer."),
            ("Do I have to use the insurer's expert?",
             "No. As the injured party you may commission an independent expert of your choice."),
        ],
        "related": ["en/services/liability-damage-report", "en/why-an-expert-report", "en/services"],
    },
    {
        "slug": "en/guide/classic-car-valuation",
        "key": "oldtimer",
        "short": "Classic car valuation report",
        "published": "2026-10-11", "modified": "2026-10-11",
        "title": "Classic Car Valuation Report: When It Pays | PS Schneider",
        "desc": "Valuation report for classic cars: when it makes sense, what it contains and how it helps with buying, selling, insurance and inheritance. Expert in Celle.",
        "h1": "Classic car valuation report: when it pays off",
        "lede": "The value of a classic car cannot be read off a list. A report makes it traceable.",
        "summary": "A valuation report determines the real market value of your classic car and documents its condition, equipment and previous and old damage. It helps when buying and selling, for protection vis-à-vis the insurer and wherever a documented value is needed.",
        "sections": [
            {"h2": "Why classic cars are special", "body": [
                "With classic cars, condition, originality, history and rarity determine the price. Two seemingly identical vehicles can differ considerably in value. Standard price lists reach their limits here.",
            ]},
            {"h2": "When a valuation report is worthwhile", "body": [
                ("ul", [
                    "When buying, to put the price into perspective and to spot hidden defects",
                    "When selling, to prove the price and offer interested buyers transparency",
                    "For protection, because insurers often ask for proof of value and condition for classic cars",
                    "In the case of an inheritance or a division of assets",
                    "Before damage occurs, so that the condition has been documented",
                ]),
            ]},
            {"h2": "What the report contains", "body": [
                ("ul", [
                    "The determined value of the vehicle",
                    "The condition, documented in writing and with photos",
                    "Special equipment and particularities",
                    "Previous and old damage",
                ]),
                "More about the procedure can be found under [[en/services/valuation-report|valuation report]]. Feel free to arrange an appointment.",
            ]},
        ],
        "faq": [
            ("How long is a valuation report valid?",
             "A report describes the value at the time of the inspection. Because markets and condition change, it should be updated after a longer period."),
            ("What does a valuation report for a classic car cost?",
             "That depends on the effort involved. You receive an individual quote in advance."),
            ("Do you also prepare reports for motorcycles?",
             "Yes. I prepare valuation reports for cars, lorries, commercial vehicles, motorcycles, classic cars and electric bicycles."),
        ],
        "related": ["en/services/valuation-report", "en/services/evidence-report", "en/guide/vehicle-report-cost"],
    },
]

AREA_LABEL = "Celle district and a 50 km radius"

AREA_REGIONS = [
    ("Celle district", "Celle and the places across the whole district."),
    ("Hanover region", "The northern and eastern part of the region up to the state capital."),
    ("Gifhorn district", "The eastern surroundings as far as Gifhorn and Wittingen."),
    ("Heidekreis district", "The north-western and northern surroundings, from Walsrode to Soltau."),
    ("Peine district", "Peine in the south-east."),
]

# German region -> English region
REGION_EN = {
    "Landkreis Celle": "Celle district",
    "Region Hannover": "Hanover region",
    "Landkreis Gifhorn": "Gifhorn district",
    "Heidekreis": "Heidekreis district",
    "Landkreis Peine": "Peine district",
}
KIND_EN = {"Stadt": "town", "Gemeinde": "municipality", "Landeshauptstadt": "state capital", "Kreisstadt": "district seat"}
NAME_EN = {"Hannover": "Hanover"}


def localize_towns(towns):
    """English copy of the town list: names, regions and kinds in English, coordinates unchanged."""
    out = []
    for t in towns:
        n = dict(t)
        n["name"] = NAME_EN.get(t["name"], t["name"])
        n["region"] = REGION_EN[t["region"]]
        if "kind" in n:
            n["kind"] = KIND_EN[n["kind"]]
        n["key"] = "town-" + t["name"]       # same key in both languages: German name
        out.append(n)
    return out
