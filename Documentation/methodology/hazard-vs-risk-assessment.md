# 🌡️ Hazard vs Risk assessment

{% hint style="info" %}
**Too Long To Read (TLDR)**

OpenChemFacts :&#x20;

* currently provides hazard values (effect factors),
* will soo provide risk values (characterization factors).

These metrics are complementary because hazard shows the inherent toxicity of a substance, while risk reflects its actual likelihood to cause environmental harm.
{% endhint %}

## 🧪Hazard&#x20;

_Hazard refers to the intrinsic potential of a substance to cause harm._

OpenChemFacts provides Effect Factors (EF) for all chemicals. These values express the inherent toxicity of a chemical independent of exposure (more info about the method [here](https://openchemfacts.gitbook.io/openchemfacts-docs/~/revisions/Sd2VKue5Sah35cbvyIrZ/methodology/effect-factor)). This is illustrated in the interface with the dose–response relationship (cf. Species-Sentivity Distribution curve).&#x20;

These information help answer such questions :&#x20;

* _How toxic is the substance?_
* _What concentration causes effects in organisms?_
* _How does biological response change with dose?_

{% hint style="info" %}
For example a pesticide can be _highly toxic_ (high EF), even if no organism is actually exposed to it.&#x20;

That is why it's usefull to combine hazard assessment with risk assessment.&#x20;
{% endhint %}

## ⚠️Risk

_Risk refers to the likelihood that harm will occur under real-world exposure conditions._

OpenChemFacts will soon provide Characterization Factors (CF) for all chemicals.&#x20;

Details are available [here](https://openchemfacts.gitbook.io/openchemfacts-docs/~/revisions/GZmw9rLEierNKSmUcTNe/methodology/usetox).&#x20;

These information help answer such questions :&#x20;

* _How harmful is this chemical to ecosystems if it is emitted into the environment ?_&#x20;
* _Which environmental compartments (air, water, soil) will receive most of the pollutant?_
* _How much of the emitted chemical will actually reach and affect organisms ?_&#x20;

