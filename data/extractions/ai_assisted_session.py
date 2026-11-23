"""Cells for the 8 reachable documents, written by an AI assistant from the hash-verified excerpts in data/excerpts/.

This is the extractor of record for the published run (the Groq extractor in largeload/extract.py
could not be called from the build sandbox). Rules followed: use only the excerpt text, copy quotes
verbatim, prefer the lower status when unsure, and mark an attribute not_addressed when the retrieved
excerpts do not support it. Every cell still goes through largeload.guard before it is counted.
"""
E, P, M, N = "explicit_provision", "planned_or_recommended", "mentioned_only", "not_addressed"
ATTRS = ["demand_quantified", "cost_allocation", "dedicated_tariff", "financial_commitment",
         "interconnection_process", "flexibility", "self_supply", "siting_limits"]


def c(attr, status, page=None, quote=None, values=(), note=""):
    return {"attribute": attr, "status": status, "page": page, "quote": quote, "values": list(values), "note": note}


NJ_NEW_LOAD = ("New load from data centers will enter the PJM system rapidly, and PJM can create new mechanisms to help "
               "accelerate the deployment of new resources. However, to the extent that new load enters the system before "
               "matching new generation, PJM must also ensure the new load enters the system flexibly to protect ratepayer "
               "costs and grid reliability.")

CELLS = {
    "nj-2024-emp": [
        c("demand_quantified", E, 7, "30 of the 32 GW of projected load growth by 2030 is associated with large load data center construction in the PJM region",
          ["30 GW", "32 GW", "2030"], "PJM forecast cited by the plan"),
        c("cost_allocation", P, 9, NJ_NEW_LOAD, [], "Expectation placed on PJM, not a state rule"),
        c("dedicated_tariff", N),
        c("financial_commitment", N),
        c("interconnection_process", M, 9,
          "The ongoing Large Load Critical Issue Fast Path charge at PJM is the most direct process addressing the issue, but load forecasting, interconnection processes, and market structure must also broadly be considered.",
          [], "Points to a PJM process"),
        c("flexibility", P, 9, NJ_NEW_LOAD, [], "Same sentence as cost_allocation; calls for flexible entry of new load"),
        c("self_supply", N),
        c("siting_limits", N),
    ],
    "me-2025-energy-plan": [c(a, N, note="Only one page mentions an anchor term (AI as a grid tool); no large-load provision retrieved") for a in ATTRS],
    "va-2026-energy-plan": [
        c("demand_quantified", E, 114, "VEP modeling projects that data centers could account for more than 90% of the Commonwealth's electricity-demand growth over the next two decades.",
          ["90%"]),
        c("cost_allocation", E, 114, "Continuing to implement robust protections and cost allocation practices will be essential to protect residential, small businesses, and other ratepayers from the infrastructure costs caused by data centers.",
          [], "States a principle"),
        c("dedicated_tariff", E, 42, "The SCC has created a separate large load rate class for Dominion Energy Virginia and related service terms for qualifying large load customers",
          [], "Effective 2027 per the plan"),
        c("financial_commitment", E, 42, "qualifying large load customers, including a 14-year contract term, minimum demand charges, collateral requirements, and exit-fee provisions, effective January 1, 2027.",
          ["14"], ""),
        c("interconnection_process", P, 42, "the SCC directed revisions to Dominion's proposed large load connection queue",
          [], "Ongoing proceeding"),
        c("flexibility", M, 96, "The Distributed Flexibility Scenario assumes all data centers provide the equivalent of a 10% reduction in peak demand.",
          ["10%"], "Modeled scenario, not an adopted rule"),
        c("self_supply", P, 118, "this could include promoting large load offtake models, large multi-unit orderbooks, ring-fenced subsidiary investment",
          [], "Nuclear financing structures"),
        c("siting_limits", N),
    ],
    "or-2025-energy-strategy": [
        c("demand_quantified", M, 89, "Although new tech loads, such as data centers, are expected to be the biggest near-term driver of electricity demand growth, relatively little information is available for these loads",
          [], "No figure given"),
        c("cost_allocation", M, 89, "Yet federal law restricts BPA's ability to supply new large loads at its lowest rates. Any service to those loads by BPA would be at a much higher rate that covers the full cost of that service or would be served by an alternative power supply that the COUs procure.",
          [], "Describes federal/BPA treatment"),
        c("dedicated_tariff", N),
        c("financial_commitment", M, 116, "Investment support from non-utility entities, particularly new large loads with significant interest in transmission upgrades, could be key to stretching limited utility and other capital.",
          [], "Suggests large loads could fund transmission"),
        c("interconnection_process", N),
        c("flexibility", M, 67, "New loads driven primarily by data centers and electrification must be integrated with an increasing supply of renewable energy resources with variable power outputs. Demand response (DR) programs allow customers to play a role in balancing grid operations",
          [], "General DR text beside data-center text"),
        c("self_supply", N),
        c("siting_limits", N),
    ],
    "ut-energy-innovation-plan-summary": [c(a, N, note="Two-page summary; no anchor term on any page") for a in ATTRS],
    "pacificorp-2025-irp-vol1": [
        c("demand_quantified", M, 22, "a sensitivity analysis evaluates the impacts of significant new data center loads coming online in the 2027-2033 timeframe",
          ["2027-2033"], "Sensitivity analysis; no MW figure in the retrieved text"),
        c("cost_allocation", N, note="Relevant sentence was cut off in the excerpt; not scored"),
        c("dedicated_tariff", N),
        c("financial_commitment", N),
        c("interconnection_process", N),
        c("flexibility", E, 145, "PacifiCorp has had interruptible contracts with large load customers for many years. These contracts are a key aspect of the retail service provided to the associated customers",
          [], "Existing interruptible contracts"),
        c("self_supply", M, 247, "driven by lower projected demand from new large customers who are expected to bring their own resources, thus lowering the commercial forecast.",
          [], "Planning assumption in the load forecast"),
        c("siting_limits", N),
    ],
    "dominion-2026-irp-update": [
        c("demand_quantified", E, 233, "The Company has seen unprecedent levels of growth in both the size and number of requests for delivery points in the last several years, including the significant increase in volume and increased size from large-\nload customers. As of February 2026, approximately 25,000 megawatts of large-load delivery point requests",
          ["25,000"], "Requests received as of Feb 2026"),
        c("cost_allocation", E, 13, "To ensure data centers and other high load customers continue to pay their fair share and to mitigate against stranded costs, the Company proposed, and the SCC approved, a robust package of cost allocation, rate design, and Terms and Conditions changes",
          [], "SCC-approved package per the utility"),
        c("dedicated_tariff", E, 13, "To ensure data centers and other high load customers continue to pay their fair share and to mitigate against stranded costs, the Company proposed, and the SCC approved, a robust package of cost allocation, rate design, and Terms and Conditions changes in the Company's biennial review proceeding, Case No. PUR-2025-00058. Notably, the Company's proposals included the creation of a new customer class for its most energy-intensive customers.",
          [], "New customer class (GS-5)"),
        c("financial_commitment", E, 235, "Execution of this agreement protects the Company, as discussed below, allows the distribution team to add the data center project to our queue, and begins the engineering study and design processes that are prerequisites to connect to the grid. At signing, a $250,000 deposit is required",
          ["$250,000"], "Deposit at ELOA signing"),
        c("interconnection_process", E, 234, "The connection process begins when a data center submits a request for service to Dominion Energy's distribution team. The request must include a site plan or building layout, requested energization date, the capacity being requested including a ramp schedule, and meter voltage",
          [], "Request, ELOA, queue"),
        c("flexibility", N),
        c("self_supply", P, 42, "the Company is evaluating potential financing approaches and commercial structures, including arrangements with third parties and large-load customers, that may improve project economics",
          [], "SMR financing with large-load customers"),
        c("siting_limits", N),
    ],
    "dominion-2025-irp-update": [
        c("demand_quantified", E, 26, "As of July 31, 2025, the Company has 16,913 MW of requested capacity under firm contracts through executed ESAs or CLOAs. The Company is currently studying an additional 30,132 MW of data center capacity at the ELOA stage.",
          ["16,913 MW", "30,132 MW"], "As of July 2025"),
        c("cost_allocation", N),
        c("dedicated_tariff", N),
        c("financial_commitment", E, 26, "The Company uses a three-contract structure with large load customers that bind customers to increasing financial commitments as projects progress.",
          [], "ESA, CLOA, ELOA"),
        c("interconnection_process", M, 51, "interconnect data center customers", [], "Transmission action item only"),
        c("flexibility", P, 27, "Dominion Energy continues to explore opportunities for and interest in demand response programs with its largest customers. To date, data centers have been hesitant to participate in demand response",
          [], "Exploring; customers hesitant"),
        c("self_supply", N),
        c("siting_limits", N),
    ],
}

CELLS["ny-2025-sep-summary"] = [
    c("demand_quantified", M, 40, "new large loads, such as manufacturing and data center projects interconnecting to the system, drive growing electricity demand across both annual loads and peaks",
      [], "Direction of demand only; figures are in Vol. II"),
    c("cost_allocation", E, 82, "New Y ork's interconnection process for new large loads is designed to fairly allocate energy system build-out or upgrade costs to the user that necessitates such costs, consistent with \u201cbeneficiary pays\u201d cost-causation principles.",
      [], "Beneficiary-pays principle; quote keeps the PDF text-layer spelling \"Y ork\""),
    c("dedicated_tariff", N, note="Recommends new rate designs for industry generally; the excerpt has no large-load anchor term beside it"),
    c("financial_commitment", N),
    c("interconnection_process", E, 82, "New Y ork's interconnection process for new large loads is designed to fairly allocate energy system build-out or upgrade costs to the user that necessitates such costs",
      [], "Same sentence as cost_allocation"),
    c("flexibility", M, 82, "Planning considerations for large data centers are complex, as uncertainty exists around their location, long-term energy consumption, and demand flexibility.",
      [], "Names flexibility as an uncertainty"),
    c("self_supply", N),
    c("siting_limits", N),
]
CELLS["ny-2025-sep-electricity"] = [
    c("demand_quantified", E, 59, "These large loads include data centers, semiconductor manufacturing plants, and green hydrogen production plants. The 2025 Gold Book indicated that large load facilities could contribute up to 19,200 GWh of additional annual energy consumption, 2,567 MW of summer peak demand, and 2,600 MW of winter peak demand in New York State by 2035",
      ["19,200 GWh", "2,567 MW", "2,600 MW", "2035"], "NYISO Gold Book figures"),
    c("cost_allocation", P, 76, "Continue to evaluate the impact of large load customers and take necessary steps to support consumers.",
      [], "Recommendation"),
    c("dedicated_tariff", N),
    c("financial_commitment", N),
    c("interconnection_process", E, 47, "The NYISO interconnection process ensures open access to the transmission grid for new generators, transmission projects, and certain large loads seeking to connect. Most proposed new projects must adhere to the NYISO interconnection process.",
      [], "Applies to certain large loads"),
    c("flexibility", N),
    c("self_supply", N),
    c("siting_limits", N),
]
CELLS["ny-2025-sep-pathways"] = [
    c("demand_quantified", E, 25, "Several large manufacturing and data-center projects are expected to enter service this coming decade. By 2040, new industrial projects are expected to demand approximately 16 TWh of electricity annually, equivalent to 75% of the industrial electricity demand today.",
      ["16 TWh", "2040", "75%"], "Figure covers new industrial projects, including data centers"),
] + [c(a, N) for a in ATTRS[1:]]
