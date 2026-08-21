# Automatic AOV Builder

> Automatically build an organized AOV compositing tree in Foundry Nuke.

[![Nuke](https://img.shields.io/badge/Nuke-17.0+-blue)](https://www.foundry.com/products/nuke)
[![Python](https://img.shields.io/badge/Python-3.x-yellow)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Automatic AOV Builder is a Python tool for Foundry Nuke designed to speed up the process of rebuilding a Beauty pass from multiple AOVs contained in a multilayer EXR.

Instead of manually creating and connecting multiple Shuffle and Merge nodes, the tool automatically creates and organizes the required node network.

The generated network remains fully editable inside Nuke.

---

## ✨ Features

- Automatic AOV categorization
- Shuffle2 node generation
- Merge2 node generation
- Beauty pass reconstruction
- Automatic node positioning
- Dot node generation
- Automatic Backdrop creation
- AOV grouping
- Unknown AOV detection
- Non-destructive workflow
- Fully editable Nuke node graph

---

## 🧩 How It Works

The tool takes a multilayer EXR and builds an organized compositing tree.

### Input

A typical multilayer EXR might contain:

```text
Read1
 ├── diffuse_direct
 ├── diffuse_indirect
 ├── specular_direct
 ├── specular_indirect
 ├── transmission_direct
 ├── transmission_indirect
 ├── sss_direct
 └── sss_indirect
