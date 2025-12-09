# 📏 Nomenclature

## Identifiers

OpenChemFacts uses InChIKey as main chemicals identifier.&#x20;

InChIKey is a hashed version of the full InChI (International Chemical Identifier). It was designed for easy web searches of chemical compounds

InChI is a textual representation of chemical substances created by the International Union of Pure and Applied Chemistry (IUPAC). It was created to provide a standard way to encode molecular information and to facilitate the search for such information in databases and on the web.

<details>

<summary>Illustration</summary>

<figure><img src="../.gitbook/assets/image (3).png" alt=""><figcaption></figcaption></figure>

</details>

## Classification

{% hint style="info" %}
Classification is usefull as it facilitates analytics.&#x20;

A first classification is available : Classyfire.
{% endhint %}

### Classyfire

Classyfire is a structural classification of chemical entities covering 4825 chemicals classes. It provides a hierarchical chemical classification for all known chemical compounds (including small molecules, peptides and peptide sequences) as well as a structure-based textual description.

<details>

<summary>Details</summary>

Classes used in OpenChemFacts :&#x20;

* Kingdom
  * organic compounds\
    def : _chemical compounds whose structure contains one or more carbon atoms_
  * inorganic compounds\
    def : _compounds that are not organic_
* SuperClass
  * 26 organic categories
  * 5 inorganic categories
* Class\
  Includes 764 classes containing >100,000 compounds
* SubClass\
  Includes 1,729 subclasses containing >10,000 compounds

<figure><img src="../.gitbook/assets/Classyfire _ illustration.png" alt=""><figcaption></figcaption></figure>

</details>
