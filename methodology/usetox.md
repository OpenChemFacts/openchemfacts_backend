# 💎 USEtox

## What is USEtox ?

USEtox is a scientific model developed to assess the toxic impacts of chemical substances on human health and the environment within the framework of Life Cycle Assessment (LCA).

It is considered the consensus model recommended by the UNEP/SETAC Life Cycle Initiative for characterizing aquatic ecotoxicity and human toxicity in LCA studies.

## How does it work?

USEtox provides characterization factors (CFs) that quantify the potential impact of a chemical substance released into the environment. For aquatic ecotoxicity, the method estimates the potential harm a substance may cause to freshwater ecosystems by considering:

* **Fate** – how the substance is distributed in different environmental compartments (air, water, soil, sediment).
* **Exposure** – the concentration of the substance organisms are exposed to in these compartments.
* **Effect** – the toxic response of organisms to the substance (e.g., mortality, reduced growth, or reproduction).

The combination of these factors results in a characterization factor (CF) for ecotoxicity, typically expressed as comparative toxic units (CTUe), which represent the potential fraction of species affected in freshwater ecosystems per unit mass of chemical emitted.

$$
CF  = FF * XF * EF
$$

<details>

<summary>Details</summary>

* CF = Characterization Factor (expressed in [_CTUe_](#user-content-fn-1)[^1] _/ kg emitted_)\
  Represents the potential ecotoxicological impact of a chemical in the environment, integrating hazard and exposure. It reflects the potentially affected fraction of species (PAF) integrated over time and volume, per unit of chemical emitted (PAF x m3 x day per kg emitted)
* FF = Fate Factor (expressed in _kg\_to\_compartment / kg\_inventory/d_)\
  Describes the environmental distribution, persistence, and transport of the chemical across compartments (air, water, soil). A high FF indicates that the substance remains longer in the environment or spreads across compartments, increasing the likelihood of exposure.
* XF = Exposure Factor (expressed in _kg\_bioavailable / kg\_to\_compartment_)\
  Quantifies how much of the chemical actually reaches ecological receptors (e.g., aquatic organisms, soil species). It represents the bioavailable mass fraction in the compartment of exposed ecosystems. It considers important processes which lower chemical concentration.&#x20;
* EF = Effect Factor (expressed in PAF m3 / kg)\
  Represents the hazard, i.e., the dose–response relationship derived from ecotoxicological data.\
  It describes how harmful the substance is to organisms once exposure occurs.

</details>

## USEtox in LCA

In Life Cycle Assessment, USEtox is used to translate chemical emissions along the life cycle of a product (from raw material extraction to end-of-life) into quantified ecotoxic impacts.

This integration allows companies, researchers, and policy makers to:

* Identify substances with high ecotoxicity potential,
* Compare alternative materials and processes,
* Support **eco-design strategies** by choosing safer or less impactful substances,
* Communicate environmental performance with standardized and transparent indicators.

## Why USEtox in OpenChemFacts?

By including USEtox characterization factors in OpenChemFacts, the project enables:

* Open access to ecotoxicity data for a wide range of chemicals,
* Easier integration of ecotoxicity assessment into eco-design and sustainability tools,
* Consistency with international LCA practices, ensuring that impact results are comparable and scientifically robust.

[^1]: Comparative Toxic Units
