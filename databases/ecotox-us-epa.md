# Ecotox (US EPA)&#x20;

{% hint style="info" %}
The **ECOTOX database**, developed by the U.S. EPA, is publicly available application that provides information on adverse effects of single chemical stressors to ecologically relevant aquatic and terrestrial species.&#x20;

Data are curated from scientific literature after an exhaustive search protocol. Compiled from over 53,000 references, ECOTOX currently includes over one million test records covering more than 13,000 aquatic and terrestrial species and 12,000 chemicals.

Detailed information [here](https://www.epa.gov/comptox-tools/ecotoxicology-ecotox-knowledgebase-resource-hub)
{% endhint %}

### What has been done ?

ECOTOX datasets have been collected locally through a SQLite database using an R package (more info [here](https://pepijn-devries.github.io/ECOTOXr/articles/ecotox-schema.html\))).&#x20;

#### Data Pipeline (summary)

| Dataset                                 | CAS    | Tests   | Results   |
| --------------------------------------- | ------ | ------- | --------- |
| All chemicals in ECOTOX                 | 18 481 | 723 445 | 1 218 861 |
| Chemicals with tests results in EC10eq  | 10 278 | 392 821 | 694 662   |
| Chemicals with relevant endpoints       | 7 182  | 244 074 | 488 837   |
| Chemicals with valid results (filtered) | 5 116  | 173 977 | 328 430   |
| Only one EC10eq result per test         | 3 617  | 87 358  | 87 358    |
