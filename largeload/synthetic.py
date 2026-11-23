"""SYNTHETIC documents for tests and guard fault-injection. Fictional text; never used for findings.

Each document is filler policy prose with provisions planted at known pages, so ground truth is known
by construction. Some planted sentences are split by PDF-style hyphenated line breaks.
"""
import random

FILLER = [
    "The department will continue to coordinate with regional planning bodies on long-term resource adequacy.",
    "Stakeholder workshops were held in each region during the planning period.",
    "Reliability metrics remain within historical ranges for the reporting period.",
    "Energy efficiency programs reduced residential consumption in the base year.",
    "The commission reviews filings on a rolling schedule and publishes orders on its docket.",
    "Transmission owners reported completion of scheduled maintenance outages.",
    "Heating demand varies with weather and is expected to remain the dominant winter driver.",
    "Funding for weatherization was allocated across counties according to need.",
]
PLANTED = {
    "demand_quantified": {
        "explicit_provision": "Data center demand is forecast to add {n} MW of peak load by {y}.",
        "mentioned_only": "Data centers are a growing source of electricity demand in the region.",
    },
    "cost_allocation": {
        "explicit_provision": "Costs of new infrastructure built to serve large loads shall be assigned to those customers and not to other ratepayers.",
        "planned_or_recommended": "The commission should examine how to keep other customers from bearing costs created by data center growth.",
    },
    "dedicated_tariff": {
        "explicit_provision": "A dedicated large load tariff applies to new customers above {n} MW.",
        "planned_or_recommended": "Utilities are directed to propose a rate class for large load customers within {n} months.",
    },
    "financial_commitment": {
        "explicit_provision": "Large load customers must sign contracts of at least {n} years with a minimum demand charge and post collateral.",
        "planned_or_recommended": "The plan recommends exploring take-or-pay terms for large loads.",
    },
    "interconnection_process": {
        "explicit_provision": "Large load interconnection requests above {n} MW enter a cluster study with a defined timeline.",
        "mentioned_only": "Interconnection of large loads has lengthened wait times for some projects.",
    },
    "flexibility": {
        "explicit_provision": "Data center customers receiving service under this schedule must curtail up to {n} percent of load during emergencies.",
        "planned_or_recommended": "Demand response participation by large loads will be evaluated in the next planning cycle.",
    },
    "self_supply": {
        "explicit_provision": "Data center developers must procure new clean generation equal to {n} percent of their annual consumption.",
        "planned_or_recommended": "The state will study co-location of generation with large loads.",
    },
    "siting_limits": {
        "explicit_provision": "A moratorium on new data center interconnections applies in constrained zones until {y}.",
        "mentioned_only": "Siting of data centers raises land and water use questions in some counties.",
    },
}
DISTRACTORS = ["Several large customers expressed interest in the new program.",
               "A data center operator attended the workshop as an observer."]


def build_doc(seed, n_pages=36, p_present=0.7):
    rng = random.Random(seed)
    pages = {i: [rng.choice(FILLER) for _ in range(rng.randint(5, 8))] for i in range(1, n_pages + 1)}
    truth = {}
    for attr, opts in PLANTED.items():
        if rng.random() > p_present:
            continue
        status = rng.choice(sorted(opts))
        sent = opts[status].format(n=rng.choice([20, 25, 50, 75, 100, 150, 300, 1200]), y=rng.choice([2028, 2030, 2035]))
        pg = rng.randint(3, n_pages)
        pos = rng.randint(0, len(pages[pg]))
        pages[pg].insert(pos, sent)
        truth[attr] = {"status": status, "page": pg, "quote": sent}
    for _ in range(3):
        pages[rng.randint(1, n_pages)].append(rng.choice(DISTRACTORS))
    out = []
    for no in sorted(pages):
        text = "\n".join(pages[no])
        if rng.random() < 0.4:   # PDF-style hyphenated line break inside a long word
            for w in ("electricity", "infrastructure", "generation"):
                if w in text:
                    text = text.replace(w, w[:6] + "-\n" + w[6:], 1)
                    break
        out.append((no, text))
    return out, truth
