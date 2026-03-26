# AXIOM Experiment Prompt Corpus

**Total prompts:** 500
**Corpus version:** 1.0
**Generated:** 2026-03-25T20:17:31Z
**Seed:** 42
**Trimming:** Removed 76 combinations: all 48 standard+terse and 28 edge_case+terse (least informative for the experiment)

---

## P-001

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 77.9 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 176 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum

---

## P-002

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell with the following requirements:
> - Capacity: 83.5 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 157 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 45 deg C
> - Target cycle life: 1500 cycles

---

## P-003

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a premium smartphone with all-day battery life. We've selected NMC-811. Performance-wise, it should retain at least 80% health after 500 charge cycles. Size-wise, it needs to be as thin as possible for a slim laptop design. We need to hit a specific price point, so don't over-engineer it.

---

## P-004

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a pouch NMC-811 cell, 50 Ah, targeting grid storage.

---

## P-005

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for an industrial-grade impact wrench. We want a good balance of cost, safety, and performance. The cell must run a high-torque drill for at least 45 minutes continuously. It also has to keep total pack weight under 800 grams. We may iterate on this, so give us a good starting point.

---

## P-006

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 cylindrical cell:
> - Capacity: approximately 12.3 Ah
> - Nominal voltage: 3.65 V
> - Application: consumer electronics battery
> - Cycle life: 500 cycles

---

## P-007

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our client wants a commercial peak-shaving installation. We want a good balance of cost, safety, and performance. The cells need to tolerate extended float-charge periods without calendar aging issues. We'd prefer to be designed for easy field replacement of individual cells. We need this design finalized by end of quarter.

---

## P-008

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP pouch cell:
> - Capacity: 6.5 Ah (nominal)
> - Nominal voltage: 3.2 V
> - Energy density: targeting 162 Wh/kg
> - Application: consumer electronics battery

---

## P-009

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell with the following requirements:
> - Capacity: 90.2 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 279 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 45 deg C
> - Target cycle life: 1500 cycles

---

## P-010

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell:
> - Capacity: approximately 111.1 Ah
> - Nominal voltage: 3.65 V
> - Energy density: 258 watt-hours per kilogram
> - Application: electric vehicle traction battery
> - Temperature range: -20 deg C to 45 deg C

---

## P-011

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell with the following requirements:
> - Capacity: 2.1 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 173 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -15 deg C to 54 deg C
> - Target cycle life: 1340 cycles

---

## P-012

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-811 cell, 4.7 Ah, targeting power tools.

---

## P-013

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a landscaping leaf blower? It should not overheat during continuous heavy-load operation, and needs to keep total pack weight under 800 grams. We've already locked in the module architecture, so the cell needs to fit.

---

## P-014

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you help design a cell for a high-performance electric sports car? The cathode should be NMC-622. It needs to support regenerative braking at moderate C-rates. We'd like it to not exceed 250 kg for the full module. Thermal management is handled at the pack level, so focus on the cell.

---

## P-015

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We've been asked to source cells for a microgrid for an off-grid community. They have to handle 5000+ deep discharge cycles without significant degradation. Cost-wise we want to be designed for easy field replacement of individual cells. We need this design finalized by end of quarter.

---

## P-016

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C2 |

**Prompt:**

> Please generate a complete cylindrical cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 11.7 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 251 Wh/kg
>   Temperature range: 0 deg C to 40 deg C
>   Cycle life requirement: 500 cycles minimum
> - Continuous discharge rate: 4.9C

**Contradiction:** Requesting 251.4 Wh/kg energy density with 4.9C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-017

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a pouch NMC-111 cell, 10 Ah, targeting power tools.

---

## P-018

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> Generate parameters for a pouch NMC-111 cell, 61.1 Ah, targeting EV traction.

**Contradiction:** Using a 5.0 micron separator with 5.1C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-019

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> Design a NMC-622 cylindrical cell with the following requirements:
> - Capacity: 6.7 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 233 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -40 deg C to 50 deg C
> - Target cycle life: 1000 cycles
> - Continuous discharge rate: 4.5C

**Contradiction:** Operating at -40 deg C with 4.5C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-020

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell:
> - Nominal voltage: 3.65 V
> - Energy density: 237 watt-hours per kilogram
> - Application: electric vehicle traction battery
> - Cycle life: 1500 cycles

---

## P-021

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Design a 131 Ah NMC-811 prismatic cell for grid storage.

**Contradiction:** Operating at -40 deg C with 4.2C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-022

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-622 prismatic battery: 50 Ah, consumer electronics use.

---

## P-023

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a utility-scale renewable integration project and need cells that can last at least 10 years of daily cycling. Range is everything here — maximize energy per kilogram. For the installation, we want to minimize cooling requirements for passive thermal management. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-024

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a landscaping leaf blower? Safety and thermal stability are paramount. It should deliver sustained high current draw for burst torque, and needs to use a compact form factor that doesn't unbalance the tool. The R&D team wants to push boundaries on this one.

---

## P-025

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 pouch cell:
> - Capacity: 10.1 Ah (nominal)
> - Nominal voltage: 3.65 V
> - Application: consumer electronics battery

---

## P-026

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C6 |

**Prompt:**

> NMC-111 cylindrical, 63.6 Ah for EV traction. Full design please.

**Contradiction:** Requesting 2.23 V nominal voltage with 221.3 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-027

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PO5, PO7 |

**Prompt:**

> We need a high-capacity pouch cell — around 185.1 Ah — but the packaging needs to be as slim as possible for a tablet for professional use. Can we minimize the edge sealing area to under a millimeter? Safety certification is a top priority.

**Contradiction:** A 185.1 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-028

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We're making an industrial-grade impact wrench and need battery cells. They need to charge from dead to full in under an hour. Form factor should use a compact form factor that doesn't unbalance the tool. We may iterate on this, so give us a good starting point.

---

## P-029

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 cylindrical cell with the following requirements:
> - Capacity: 10 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 191 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 1000 cycles

---

## P-030

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell:
> - Capacity: 55.3 Ah (nominal)
> - Nominal voltage: 3.7 V
> - Energy density: targeting 173 Wh/kg
> - Application: electric vehicle traction battery

---

## P-031

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Our product team needs a battery for a next-generation foldable phone. We're planning on NMC-111 chemistry. The battery must keep surface temperature below 42 degrees C during fast charge, and we need it to be as thin as possible for a slim laptop design. We're on a tight timeline for this.

---

## P-032

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We've been asked to source cells for a grid-scale frequency regulation unit. Longevity and safety matter more than energy density. They have to tolerate extended float-charge periods without calendar aging issues. Cost-wise we want to minimize cooling requirements for passive thermal management. The customer has asked for a conservative design.

---

## P-033

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Need a cylindrical cell: NMC-811, around 50 Ah, for EV traction application.

---

## P-034

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 2.8 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 175 Wh/kg
>   Temperature range: -11 deg C to 50 deg C
>   Cycle life requirement: 1587 cycles minimum

---

## P-035

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> Please generate a complete prismatic cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-811 (LiNi0.8Mn0.1Co0.1O2)
>   Cell capacity: 5.7 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 244 Wh/kg
>   Temperature range: -40 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum
> - Continuous discharge rate: 4.9C

**Contradiction:** Operating at -40 deg C with 4.9C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-036

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO1, PO5 |

**Prompt:**

> Design a NMC-811 pouch cell with the following requirements:
> - Capacity: 155.5 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 255 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 40 deg C
> - Target cycle life: 500 cycles

**Contradiction:** Requesting 155.5 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-037

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for a high-performance electric sports car and we need a complete cell spec. The cell has to support regenerative braking at moderate C-rates. Also, it should not exceed 250 kg for the full module. We've already locked in the module architecture, so the cell needs to fit.

---

## P-038

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 8.1 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 147 Wh/kg
>   Temperature range: 0 deg C to 40 deg C
>   Cycle life requirement: 500 cycles minimum

---

## P-039

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C6 |

**Prompt:**

> I need a full parametric design for a NMC-811 pouch battery cell.
> 
> Requirements:
> * Target capacity: 99.5 Ah
> * Nominal voltage: 2.38 V
> * Energy density: at least 291 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -20 deg C and 45 deg C
> * Cycle life goal: 1500+

**Contradiction:** Requesting 2.38 V nominal voltage with 291.0 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-040

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We've been asked to source cells for a microgrid for an off-grid community. We're going with NMC-622. They have to tolerate extended float-charge periods without calendar aging issues. Cost-wise we want to be designed for easy field replacement of individual cells. The customer has asked for a conservative design.

---

## P-041

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | CY1, CY5 |

**Prompt:**

> We want to use standard 18650 cells for a landscaping leaf blower to keep costs down, but we need at least 96.2 Ah per cell. Our pack design is optimized for that form factor. Can it be done? We're on a tight timeline for this.

**Contradiction:** Requesting 96.2 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-042

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 cylindrical cell with the following requirements:
> - Capacity: 100 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 191 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles

---

## P-043

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO1, PO5 |

**Prompt:**

> Please generate a complete pouch cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 178.9 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 197 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum

**Contradiction:** Requesting 178.9 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-044

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> Please generate a complete cylindrical cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 56.5 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 192 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum
> - Continuous discharge rate: 5.9C
> - Maximum separator thickness: 4.0 microns

**Contradiction:** Using a 4.0 micron separator with 5.9C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-045

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> Design a 100 Ah NMC-111 prismatic cell for grid storage.

**Contradiction:** Using a 3.5 micron separator with 4.6C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-046

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a contractor's reciprocating saw used on job sites? Longevity and safety matter more than energy density. It should charge from dead to full in under an hour, and needs to be robust enough to survive drops from a 2-meter height. Thermal management is handled at the pack level, so focus on the cell.

---

## P-047

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP pouch cell with the following requirements:
> - Capacity: 284.8 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 171 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -15 deg C to 52 deg C
> - Target cycle life: 8175 cycles

---

## P-048

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> We need a cell for a portable gaming device with a nominal voltage around 2.38 V to match our legacy power electronics, but we still want best-in-class energy density — above 226 Wh/kg. Can you design something?

**Contradiction:** Requesting 2.38 V nominal voltage with 226.6 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-049

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for a high-performance electric sports car and we need a complete cell spec. Please design around NMC-811 chemistry. The cell has to deliver consistent power in both highway cruise and stop-and-go driving. Also, it should fit within a standard skateboard platform. Our manufacturing partner has experience with this form factor.

---

## P-050

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 9.8 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 172 Wh/kg
>   Temperature range: -14 deg C to 53 deg C
>   Cycle life requirement: 1740 cycles minimum

---

## P-051

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell:
> - Capacity: 113.6 Ah (nominal)
> - Nominal voltage: 3.65 V
> - Application: stationary grid energy storage
> - Temperature range: -10 deg C to 50 deg C
> - Cycle life: 5000 cycles

---

## P-052

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell:
> - Nominal voltage: 3.65 V
> - Energy density: 215 watt-hours per kilogram
> - Application: stationary grid energy storage
> - Cycle life: 5000 cycles

---

## P-053

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a LFP pouch battery: 94.9 Ah, EV traction use.

---

## P-054

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a cordless circular saw? A proven, cost-effective cathode chemistry would be ideal. It should not overheat during continuous heavy-load operation, and needs to be robust enough to survive drops from a 2-meter height. The customer has asked for a conservative design.

---

## P-055

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> NMC-111 cylindrical, 100 Ah for grid storage. Full design please.

**Contradiction:** Using a 4.5 micron separator with 4.7C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-056

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C4, C1 |

**Prompt:**

> We're deploying a professional cordless drill in northern Canada where temperatures regularly drop to -10 deg C. The vehicles still need to fast-charge at 4.5C at those temperatures. What cell design would work here? We need to hit a specific price point, so don't over-engineer it.

**Contradiction:** Using a 3.8 micron separator with 4.5C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-057

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 229.4 Ah LFP cylindrical cell for grid storage.

---

## P-058

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP pouch cell:
> - Nominal voltage: 3.2 V
> - Energy density: above 166 Wh/kg
> - Application: electric vehicle traction battery
> - Cycle life: 1500 cycles

---

## P-059

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> NMC-111 cylindrical, 10 Ah for power tools. Full design please.

**Contradiction:** Operating at -40 deg C with 3.3C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-060

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 93.5 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 208 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum

---

## P-061

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C4, C1 |

**Prompt:**

> We're deploying a mid-size EV platform for a European OEM in northern Canada where temperatures regularly drop to -20 deg C. The vehicles still need to fast-charge at 5.1C at those temperatures. What cell design would work here?

**Contradiction:** Using a 4.9 micron separator with 5.1C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-062

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 cylindrical cell with the following requirements:
> - Capacity: 138.5 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 254 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -23 deg C to 50 deg C
> - Target cycle life: 2017 cycles

---

## P-063

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell with the following requirements:
> - Capacity: 79.4 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 193 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 45 deg C
> - Target cycle life: 1500 cycles

---

## P-064

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-622 cell, 6.9 Ah, targeting power tools.

---

## P-065

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PO5, PO7 |

**Prompt:**

> We need a high-capacity pouch cell — around 179.3 Ah — but the packaging needs to be as slim as possible for a mid-size EV platform for a European OEM. Can we minimize the edge sealing area to under a millimeter? We've already locked in the module architecture, so the cell needs to fit.

**Contradiction:** A 179.3 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-066

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our engineering team needs cells for a heavy-duty angle grinder for metalwork. Main concern: deliver sustained high current draw for burst torque. Additionally, use a compact form factor that doesn't unbalance the tool. We need this design finalized by end of quarter.

---

## P-067

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 114.7 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 257 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+

---

## P-068

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 3.3 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 176 Wh/kg
>   Temperature range: -4 deg C to 41 deg C
>   Cycle life requirement: 899 cycles minimum

---

## P-069

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PR1, PR3 |

**Prompt:**

> Please generate a complete prismatic cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 199.1 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 188 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum

**Contradiction:** Requesting 199.1 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-070

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> Design a 139.3 Ah NMC-811 cylindrical cell for grid storage.

**Contradiction:** Requesting 319.0 Wh/kg energy density with 5.4C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-071

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> Please generate a complete prismatic cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 112.9 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 236 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 5000 cycles minimum
> - Continuous discharge rate: 5.6C
> - Maximum separator thickness: 3.5 microns

**Contradiction:** Using a 3.5 micron separator with 5.6C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-072

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Specify a NMC-811 pouch battery: 129.1 Ah, grid storage use.

**Contradiction:** Operating at -40 deg C with 4.4C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-073

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C4, C1 |

**Prompt:**

> We're deploying a heavy-duty angle grinder for metalwork in northern Canada where temperatures regularly drop to -10 deg C. The vehicles still need to fast-charge at 5.6C at those temperatures. What cell design would work here? The client is flexible on dimensions but firm on weight.

**Contradiction:** Using a 3.1 micron separator with 5.6C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-074

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C2 |

**Prompt:**

> Please generate a complete prismatic cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 8 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 257 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum
> - Continuous discharge rate: 5.6C

**Contradiction:** Requesting 257.4 Wh/kg energy density with 5.6C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-075

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our engineering team needs cells for a professional cordless drill. We're going with NMC-622. Main concern: charge from dead to full in under an hour. Additionally, keep total pack weight under 800 grams. We've already locked in the module architecture, so the cell needs to fit.

---

## P-076

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | CY1, CY5 |

**Prompt:**

> Please generate a complete cylindrical cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 56.2 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 146 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum
> - Format: 18650

**Contradiction:** Requesting 56.2 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-077

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell:
> - Nominal voltage: 3.65 V
> - Application: cordless power tool battery

---

## P-078

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C6 |

**Prompt:**

> Please generate a complete prismatic cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 13.7 Ah
>   Voltage: 2.45 V nominal
>   Energy density target: 245 Wh/kg
>   Temperature range: 0 deg C to 40 deg C
>   Cycle life requirement: 500 cycles minimum

**Contradiction:** Requesting 2.45 V nominal voltage with 245.2 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-079

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a residential solar energy storage system and need cells that can handle 5000+ deep discharge cycles without significant degradation. Gravimetric energy density is our top priority. For the installation, we want to use a standard module form factor for rack mounting. The R&D team wants to push boundaries on this one.

---

## P-080

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a backup power system for a data center and need cells that can tolerate extended float-charge periods without calendar aging issues. We want something that will last thousands of cycles. For the installation, we want to be designed for easy field replacement of individual cells.

---

## P-081

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our engineering team needs cells for a contractor's reciprocating saw used on job sites. A proven, cost-effective cathode chemistry would be ideal. Main concern: handle the vibration and shock of professional job site use. Additionally, keep total pack weight under 800 grams. Safety certification is a top priority.

---

## P-082

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PO1, PO5 |

**Prompt:**

> We need 91.0 Ah of capacity in the smallest possible package for a heavy-duty angle grinder for metalwork. Think credit-card-sized if possible. The device has very limited internal volume.

**Contradiction:** Requesting 91.0 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-083

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Need a pouch cell: NMC-111, around 2.4 Ah, for consumer electronics application.

---

## P-084

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 cylindrical cell:
> - Nominal voltage: 3.65 V
> - Application: cordless power tool battery
> - Cycle life: 1000 cycles

---

## P-085

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP cylindrical cell with the following requirements:
> - Capacity: 137.2 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 171 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -22 deg C to 45 deg C
> - Target cycle life: 2445 cycles

---

## P-086

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 pouch cell with the following requirements:
> - Capacity: 43.9 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 255 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 46 deg C
> - Target cycle life: 2149 cycles

---

## P-087

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> LFP cylindrical, 50 Ah for EV traction. Full design please.

---

## P-088

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-622 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 110 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 241 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+

---

## P-089

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C6 |

**Prompt:**

> I need a full parametric design for a NMC-111 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 100 Ah
> * Nominal voltage: 2.2 V
> * Energy density: at least 230 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+

**Contradiction:** Requesting 2.2 V nominal voltage with 230.1 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-090

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> Design a 109.9 Ah NMC-622 cylindrical cell for grid storage.

**Contradiction:** Requesting 251.2 Wh/kg energy density with 5.2C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-091

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO1, PO5 |

**Prompt:**

> I need a full parametric design for a LFP pouch battery cell.
> 
> Requirements:
> * Target capacity: 119 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 154 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

**Contradiction:** Requesting 119.0 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-092

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-622 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 141.8 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 253 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -21 deg C and 50 deg C
> * Cycle life goal: 2438+

---

## P-093

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-111 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 13.8 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 213 Wh/kg
> * End use: consumer electronics battery
> * Must operate between -5 deg C and 43 deg C
> * Cycle life goal: 749+

---

## P-094

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Our engineering team needs cells for an industrial-grade impact wrench. We want NMC-811 for maximum energy density. Main concern: charge from dead to full in under an hour. Additionally, keep total pack weight under 800 grams.

---

## P-095

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> Our system operates at 2.29 V per cell. For a microgrid for an off-grid community, we also need at least 275 Wh/kg. We can't change the voltage — the BMS firmware is locked to that range. We're on a tight timeline for this.

**Contradiction:** Requesting 2.29 V nominal voltage with 275.9 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-096

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 7.8 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 237 Wh/kg
>   Temperature range: 0 deg C to 40 deg C
>   Cycle life requirement: 500 cycles minimum

---

## P-097

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our team is working on an electric SUV with 500 km range target. A proven, cost-effective cathode chemistry would be ideal. We need cells that can deliver consistent power in both highway cruise and stop-and-go driving. not exceed 250 kg for the full module We need this design finalized by end of quarter.

---

## P-098

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-622 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 3 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 253 Wh/kg
> * End use: consumer electronics battery
> * Must operate between -8 deg C and 44 deg C
> * Cycle life goal: 803+

---

## P-099

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | PO5, PO7 |

**Prompt:**

> Generate parameters for a pouch NMC-111 cell, 126.7 Ah, targeting consumer electronics.

**Contradiction:** A 126.7 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-100

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Design a 140.3 Ah NMC-811 pouch cell for EV traction.

---

## P-101

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C2 |

**Prompt:**

> For a contractor's reciprocating saw used on job sites, we need a cell that can do 4.7C sustained discharge for burst performance, but we also can't compromise on energy density — we're targeting 305 Wh/kg minimum. Is there a design that can do both?

**Contradiction:** Requesting 305.5 Wh/kg energy density with 4.7C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-102

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell with the following requirements:
> - Capacity: 11.5 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 203 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 40 deg C
> - Target cycle life: 500 cycles

---

## P-103

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C4 |

**Prompt:**

> We're deploying a commercial peak-shaving installation in northern Canada where temperatures regularly drop to -40 deg C. The vehicles still need to fast-charge at 3.9C at those temperatures. What cell design would work here? Reliability over the full warranty period is essential.

**Contradiction:** Operating at -40 deg C with 3.9C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-104

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a LFP prismatic battery cell.
> 
> Requirements:
> * Target capacity: 153.7 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 147 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+

---

## P-105

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a cylindrical LFP cell, 14.3 Ah, targeting consumer electronics.

---

## P-106

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you help design a cell for an electric SUV with 500 km range target? We need the highest energy density we can get. It needs to handle DC fast charging at up to 2C without excessive degradation. We'd like it to be compact enough for a structural battery pack design. Reliability over the full warranty period is essential.

---

## P-107

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 cylindrical cell with the following requirements:
> - Capacity: 290 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 251 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 53 deg C
> - Target cycle life: 6546 cycles

---

## P-108

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> NMC-811 cylindrical, 7 Ah for consumer electronics. Full design please.

**Contradiction:** NMC-811 cycling at -35 deg C with a 8622-cycle life target is contradictory. The high-nickel cathode suffers accelerated capacity fade at low temperatures due to kinetic limitations and SEI growth.

---

## P-109

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> Our system operates at 2.31 V per cell. For a long-range electric sedan, we also need at least 244 Wh/kg. We can't change the voltage — the BMS firmware is locked to that range. Thermal management is handled at the pack level, so focus on the cell.

**Contradiction:** Requesting 2.31 V nominal voltage with 244.3 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-110

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I'm working on a commercial peak-shaving installation. We need the highest energy density we can get. Key requirement: operate reliably in an unconditioned outdoor enclosure. The cells should use a standard module form factor for rack mounting. Reliability over the full warranty period is essential.

---

## P-111

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 216 Ah LFP pouch cell for grid storage.

---

## P-112

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a landscaping leaf blower? Range is everything here — maximize energy per kilogram. It should not overheat during continuous heavy-load operation, and needs to use a compact form factor that doesn't unbalance the tool. We need to hit a specific price point, so don't over-engineer it.

---

## P-113

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete prismatic cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 144.4 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 172 Wh/kg
>   Temperature range: -27 deg C to 50 deg C
>   Cycle life requirement: 2177 cycles minimum

---

## P-114

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-811 cell, 50 Ah, targeting consumer electronics.

---

## P-115

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Looking for a battery cell for a landscaping leaf blower. We want something that will last thousands of cycles. Priority is a cell that can charge from dead to full in under an hour. As for size, it should keep total pack weight under 800 grams. This is a prototype, so cost is secondary to getting the specs right.

---

## P-116

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell with the following requirements:
> - Capacity: 107.9 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 218 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles

---

## P-117

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're building an electric SUV with 500 km range target and need a battery cell design. The cell should deliver consistent power in both highway cruise and stop-and-go driving.be compact enough for a structural battery pack design Budget is not the primary concern here — performance is.

---

## P-118

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> I need a full parametric design for a LFP prismatic battery cell.
> 
> Requirements:
> * Target capacity: 5.4 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 142 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -40 deg C and 50 deg C
> * Cycle life goal: 1000+
> - Continuous discharge rate: 3.7C

**Contradiction:** Operating at -40 deg C with 3.7C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-119

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C2 |

**Prompt:**

> For a tablet for professional use, we need a cell that can do 5.4C sustained discharge for burst performance, but we also can't compromise on energy density — we're targeting 290 Wh/kg minimum. Is there a design that can do both? The client is flexible on dimensions but firm on weight.

**Contradiction:** Requesting 290.7 Wh/kg energy density with 5.4C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-120

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> LFP pouch, 149.8 Ah for grid storage. Full design please.

**Contradiction:** Operating at -40 deg C with 3.6C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-121

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Need a cylindrical cell: NMC-622, around 5.6 Ah, for consumer electronics application.

---

## P-122

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 pouch cell with the following requirements:
> - Capacity: 11.3 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 192 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 40 deg C
> - Target cycle life: 500 cycles

---

## P-123

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 pouch cell:
> - Capacity: 65.1 Ah
> - Nominal voltage: 3.7 V
> - Application: electric vehicle traction battery
> - Cycle life: 1500 cycles

---

## P-124

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-811 cell, 50 Ah, targeting EV traction.

---

## P-125

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell:
> - Capacity: 11.4 Ah (nominal)
> - Nominal voltage: 3.65 V
> - Application: consumer electronics battery
> - Temperature range: 0 deg C to 40 deg C
> - Cycle life: 500 cycles

---

## P-126

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PR1, PR3 |

**Prompt:**

> Can we get a 166.4 Ah cell that fits in a pocket-sized enclosure? It's for a utility-scale renewable integration project and portability is everything. We want it as compact as physically possible. The customer has asked for a conservative design.

**Contradiction:** Requesting 166.4 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-127

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell:
> - Capacity: around 10.5 Ah
> - Nominal voltage: 3.2 V
> - Energy density: targeting 160 Wh/kg
> - Application: consumer electronics battery

---

## P-128

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | CY1, CY5 |

**Prompt:**

> Design a NMC-811 cylindrical cell with the following requirements:
> - Capacity: 76.4 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 249 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles
> - Format: 18650

**Contradiction:** Requesting 76.4 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-129

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for a long-range electric sedan and we need a complete cell spec. A proven, cost-effective cathode chemistry would be ideal. The cell has to support regenerative braking at moderate C-rates. Also, it should fit within a standard skateboard platform.

---

## P-130

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-111 prismatic battery: 50 Ah, EV traction use.

---

## P-131

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a professional cordless drill? We want NMC-811 for maximum energy density. It should charge from dead to full in under an hour, and needs to be robust enough to survive drops from a 2-meter height. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-132

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-622 pouch battery cell.
> 
> Requirements:
> * Target capacity: 6.4 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 211 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

---

## P-133

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I'm working on a backup power system for a data center. We prefer LFP for safety and longevity. Key requirement: handle 5000+ deep discharge cycles without significant degradation. The cells should be designed for easy field replacement of individual cells.

---

## P-134

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a pouch NMC-622 cell, 50 Ah, targeting grid storage.

---

## P-135

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell:
> - Nominal voltage: 3.65 V
> - Energy density: targeting 201 Wh/kg
> - Application: electric vehicle traction battery
> - Cycle life: 1500 cycles

---

## P-136

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> Our system operates at 2.21 V per cell. For a commercial peak-shaving installation, we also need at least 293 Wh/kg. We can't change the voltage — the BMS firmware is locked to that range. Thermal management is handled at the pack level, so focus on the cell.

**Contradiction:** Requesting 2.21 V nominal voltage with 293.6 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-137

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Need a cylindrical cell: LFP, around 9.8 Ah, for consumer electronics application.

**Contradiction:** Operating at -40 deg C with 3.1C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-138

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP pouch cell:
> - Capacity: approximately 205.3 Ah
> - Nominal voltage: 3.2 V
> - Energy density: at least 160 Wh/kg
> - Application: stationary grid energy storage
> - Cycle life: 5000 cycles

---

## P-139

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for an urban electric bus with daily fast-charge cycles and we need a complete cell spec. We want iron phosphate for this application. The cell has to maintain at least 80% capacity after 1500 full cycles. Also, it should not exceed 250 kg for the full module. We need to hit a specific price point, so don't over-engineer it.

---

## P-140

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our client wants a residential solar energy storage system. We're planning on NMC-111 chemistry. The cells need to deliver consistent round-trip efficiency above 92%. We'd prefer to prioritize cost per kWh over weight or volume. This is a prototype, so cost is secondary to getting the specs right.

---

## P-141

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C2, C6 |

**Prompt:**

> LFP pouch, 5.1 Ah for power tools. Full design please.

**Contradiction:** LFP chemistry physically cannot achieve 267.1 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-142

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're developing a tablet for professional use and need a battery cell. We want something that will last thousands of cycles. It should keep surface temperature below 42 degrees C during fast charge. Ideally it would conform to a non-rectangular cavity inside the device. We need to hit a specific price point, so don't over-engineer it.

---

## P-143

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a professional cordless drill? We want something that will last thousands of cycles. It should charge from dead to full in under an hour, and needs to fit the standard battery bay of our existing tool platform. We're on a tight timeline for this.

---

## P-144

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 67.3 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 267 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -20 deg C and 45 deg C
> * Cycle life goal: 1500+

---

## P-145

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a pouch NMC-622 cell, 9.2 Ah, targeting power tools.

---

## P-146

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Specify a LFP pouch battery: 14.7 Ah, consumer electronics use.

---

## P-147

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C2, C6 |

**Prompt:**

> Design a LFP prismatic cell with the following requirements:
> - Capacity: 71.4 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 212 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 45 deg C
> - Target cycle life: 1500 cycles

**Contradiction:** LFP chemistry physically cannot achieve 212.4 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-148

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C4 |

**Prompt:**

> Our application is a microgrid for an off-grid community that operates in Arctic conditions — we need reliable performance down to -40 deg C. It also needs to accept fast charging at 4.1C when plugged in at a remote charging station. Is that feasible? The R&D team wants to push boundaries on this one.

**Contradiction:** Operating at -40 deg C with 4.1C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-149

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> NMC-622 pouch, 108.5 Ah for grid storage. Full design please.

**Contradiction:** Operating at -40 deg C with 4.1C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-150

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> NMC-811 pouch, 104.9 Ah for EV traction. Full design please.

**Contradiction:** Using a 4.0 micron separator with 5.5C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-151

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> I need a full parametric design for a NMC-622 pouch battery cell.
> 
> Requirements:
> * Target capacity: 5.5 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 233 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+
> - Continuous discharge rate: 4.4C
> - Maximum separator thickness: 4.2 microns

**Contradiction:** Using a 4.2 micron separator with 4.4C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-152

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 cylindrical cell:
> - Capacity: approximately 137.5 Ah
> - Nominal voltage: 3.65 V
> - Application: stationary grid energy storage
> - Cycle life: 5000 cycles

---

## P-153

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 pouch battery cell.
> 
> Requirements:
> * Target capacity: 147.2 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 296 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -30 deg C and 47 deg C
> * Cycle life goal: 2482+

---

## P-154

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a cordless circular saw. We're going with NMC-622. The cell must not overheat during continuous heavy-load operation. It also has to fit the standard battery bay of our existing tool platform. The client is flexible on dimensions but firm on weight.

---

## P-155

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 cylindrical cell:
> - Capacity: 10 Ah
> - Nominal voltage: 3.7 V
> - Application: cordless power tool battery

---

## P-156

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 51 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 176 Wh/kg
>   Temperature range: -26 deg C to 49 deg C
>   Cycle life requirement: 2005 cycles minimum

---

## P-157

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> Need a prismatic cell: NMC-622, around 109.4 Ah, for grid storage application.

**Contradiction:** Requesting 292.7 Wh/kg energy density with 5.6C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-158

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C2 |

**Prompt:**

> Design a NMC-811 cylindrical cell with the following requirements:
> - Capacity: 112.7 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 337 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 45 deg C
> - Target cycle life: 11405 cycles

**Contradiction:** Targeting 337.1 Wh/kg energy density with 11405 cycle life is a fundamental tradeoff conflict. High energy density NMC-811 cathodes degrade faster due to structural instability at high states of charge.

---

## P-159

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a pouch LFP cell, 50 Ah, targeting power tools.

---

## P-160

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for a mid-size EV platform for a European OEM. We need the highest energy density we can get. Key priorities: the cell must support regenerative braking at moderate C-rates, and fit within a standard skateboard platform. The client is flexible on dimensions but firm on weight.

---

## P-161

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> I need a full parametric design for a NMC-111 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 75.7 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 194 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -40 deg C and 45 deg C
> * Cycle life goal: 1500+
> - Continuous discharge rate: 4.7C

**Contradiction:** Operating at -40 deg C with 4.7C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-162

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> LFP prismatic, 144.9 Ah for grid storage. Full design please.

---

## P-163

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for a commercial electric delivery van and we need a complete cell spec. We've selected NMC-811. The cell has to maintain at least 80% capacity after 1500 full cycles. Also, it should be compact enough for a structural battery pack design. We've already locked in the module architecture, so the cell needs to fit.

---

## P-164

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Need a pouch cell: NMC-111, around 40.8 Ah, for EV traction application.

---

## P-165

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a wireless earbud charging case. We want a good balance of cost, safety, and performance. Performance-wise, it should last a full day of heavy use without recharging. Size-wise, it needs to be as thin as possible for a slim laptop design. The R&D team wants to push boundaries on this one.

---

## P-166

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell with the following requirements:
> - Capacity: 4.2 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 148 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 1000 cycles

---

## P-167

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a microgrid for an off-grid community. We're looking for better-than-average energy density without going too aggressive. The deployment requires cells that operate reliably in an unconditioned outdoor enclosure, and we need to use a standard module form factor for rack mounting. Our manufacturing partner has experience with this form factor.

---

## P-168

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a professional cordless drill? We're looking for better-than-average energy density without going too aggressive. It should deliver sustained high current draw for burst torque, and needs to use a compact form factor that doesn't unbalance the tool. This is a prototype, so cost is secondary to getting the specs right.

---

## P-169

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a next-generation foldable phone. We want a good balance of cost, safety, and performance. Performance-wise, it should keep surface temperature below 42 degrees C during fast charge. Size-wise, it needs to be as thin as possible for a slim laptop design. Thermal management is handled at the pack level, so focus on the cell.

---

## P-170

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> Design a 120.2 Ah NMC-811 cylindrical cell for EV traction.

**Contradiction:** Targeting 307.0 Wh/kg energy density with 9640 cycle life is a fundamental tradeoff conflict. High energy density NMC-811 cathodes degrade faster due to structural instability at high states of charge.

---

## P-171

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | CY1, CY5 |

**Prompt:**

> Is it possible to design an 18650-format cell with 72.5 Ah capacity for a wireless earbud charging case? We want to leverage the existing supply chain for that format. We're on a tight timeline for this.

**Contradiction:** Requesting 72.5 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-172

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 11.4 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 168 Wh/kg
>   Temperature range: 0 deg C to 40 deg C
>   Cycle life requirement: 500 cycles minimum

---

## P-173

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> Design a LFP prismatic cell with the following requirements:
> - Capacity: 10.5 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 139 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: -40 deg C to 40 deg C
> - Target cycle life: 500 cycles
> - Continuous discharge rate: 4.0C

**Contradiction:** Operating at -40 deg C with 4.0C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-174

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for a commercial electric delivery van and we need a complete cell spec. The cell has to handle DC fast charging at up to 2C without excessive degradation. Also, it should be compact enough for a structural battery pack design. The customer has asked for a conservative design.

---

## P-175

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you help design a cell for an urban electric bus with daily fast-charge cycles? We're planning on NMC-111 chemistry. It needs to support regenerative braking at moderate C-rates. We'd like it to use a form factor compatible with CTP (cell-to-pack) architecture. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-176

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C4 |

**Prompt:**

> Our application is a mid-size EV platform for a European OEM that operates in Arctic conditions — we need reliable performance down to -40 deg C. It also needs to accept fast charging at 4.6C when plugged in at a remote charging station. Is that feasible? Our manufacturing partner has experience with this form factor.

**Contradiction:** Operating at -40 deg C with 4.6C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-177

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> NMC-622 pouch, 113.1 Ah for grid storage. Full design please.

---

## P-178

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> I need a full parametric design for a NMC-622 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 81.2 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 230 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -40 deg C and 45 deg C
> * Cycle life goal: 1500+
> - Continuous discharge rate: 3.8C

**Contradiction:** Operating at -40 deg C with 3.8C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-179

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for a high-performance electric sports car. Safety and thermal stability are paramount. Key priorities: the cell must handle DC fast charging at up to 2C without excessive degradation, and be compact enough for a structural battery pack design. This is a prototype, so cost is secondary to getting the specs right.

---

## P-180

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a wireless earbud charging case. Safety and thermal stability are paramount. Main requirement: retain at least 80% health after 500 charge cycles. For form factor, it should conform to a non-rectangular cavity inside the device. We've already locked in the module architecture, so the cell needs to fit.

---

## P-181

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP cylindrical cell:
> - Capacity: approximately 82.7 Ah
> - Nominal voltage: 3.2 V
> - Energy density: 138 watt-hours per kilogram
> - Application: electric vehicle traction battery

---

## P-182

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO1, PO5 |

**Prompt:**

> Please generate a complete pouch cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 197.9 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 142 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum

**Contradiction:** Requesting 197.9 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-183

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 108.5 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 156 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum

---

## P-184

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We've been asked to source cells for a grid-scale frequency regulation unit. We want a good balance of cost, safety, and performance. They have to handle 5000+ deep discharge cycles without significant degradation. Cost-wise we want to minimize cooling requirements for passive thermal management. The customer has asked for a conservative design.

---

## P-185

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C2, C6 |

**Prompt:**

> We need a battery for a utility-scale renewable integration project that's extremely lightweight and energy-dense — at least 243 Wh/kg. But safety is non-negotiable, so we want to stick with iron phosphate chemistry. Can you make that work? Safety certification is a top priority.

**Contradiction:** LFP chemistry physically cannot achieve 243.5 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-186

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a laptop that needs to last 12 hours. Please use LFP chemistry. Performance-wise, it should support fast charging from 0 to 80% in under 30 minutes. Size-wise, it needs to fit in a phone body under 8 mm thick. Our manufacturing partner has experience with this form factor.

---

## P-187

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C2 |

**Prompt:**

> For a high-performance electric sports car, we need a cell that can do 4.3C sustained discharge for burst performance, but we also can't compromise on energy density — we're targeting 297 Wh/kg minimum. Is there a design that can do both? This is a prototype, so cost is secondary to getting the specs right.

**Contradiction:** Requesting 297.9 Wh/kg energy density with 4.3C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-188

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell with the following requirements:
> - Capacity: 92.3 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 209 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 45 deg C
> - Target cycle life: 1500 cycles

---

## P-189

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a LFP cylindrical battery: 50 Ah, power tools use.

---

## P-190

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C2, C6 |

**Prompt:**

> Generate parameters for a pouch LFP cell, 12.4 Ah, targeting consumer electronics.

**Contradiction:** LFP chemistry physically cannot achieve 275.6 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-191

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C2 |

**Prompt:**

> I need a full parametric design for a NMC-622 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 104.1 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 298 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+
> - Continuous discharge rate: 4.6C

**Contradiction:** Requesting 298.1 Wh/kg energy density with 4.6C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-192

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our product team needs a battery for a laptop that needs to last 12 hours. Range is everything here — maximize energy per kilogram. The battery must keep surface temperature below 42 degrees C during fast charge, and we need it to be as thin as possible for a slim laptop design. Budget is not the primary concern here — performance is.

---

## P-193

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-622 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 2.3 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 250 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -13 deg C and 51 deg C
> * Cycle life goal: 1605+

---

## P-194

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-111 prismatic battery: 147.4 Ah, EV traction use.

---

## P-195

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-111 cell, 100 Ah, targeting grid storage.

---

## P-196

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 114.5 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 209 Wh/kg
>   Temperature range: -13 deg C to 50 deg C
>   Cycle life requirement: 8169 cycles minimum

---

## P-197

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 pouch cell:
> - Nominal voltage: 3.7 V
> - Application: consumer electronics battery
> - Temperature range: 0 deg C to 40 deg C

---

## P-198

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> NMC-622 pouch, 66.6 Ah for EV traction. Full design please.

---

## P-199

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO5, PO7 |

**Prompt:**

> I need a full parametric design for a NMC-111 pouch battery cell.
> 
> Requirements:
> * Target capacity: 182.6 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 195 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+
> - Maximum edge seal width: 0.9 mm

**Contradiction:** A 182.6 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-200

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're building a long-range electric sedan and need a battery cell design. Longevity and safety matter more than energy density. The cell should support regenerative braking at moderate C-rates.not exceed 250 kg for the full module Budget is not the primary concern here — performance is.

---

## P-201

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> NMC-111 prismatic, 10 Ah for power tools. Full design please.

---

## P-202

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Design a 45.6 Ah NMC-811 cylindrical cell for EV traction.

---

## P-203

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 9.7 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 290 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -14 deg C and 50 deg C
> * Cycle life goal: 1672+

---

## P-204

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 cylindrical cell:
> - Nominal voltage: 3.65 V
> - Energy density: above 216 Wh/kg
> - Application: electric vehicle traction battery
> - Cycle life: 1500 cycles

---

## P-205

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 cylindrical cell:
> - Capacity: approximately 58.5 Ah
> - Nominal voltage: 3.7 V
> - Application: electric vehicle traction battery

---

## P-206

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a commercial peak-shaving installation. We want iron phosphate for this application. The deployment requires cells that operate reliably in an unconditioned outdoor enclosure, and we need to prioritize cost per kWh over weight or volume. We've already locked in the module architecture, so the cell needs to fit.

---

## P-207

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're developing a premium smartphone with all-day battery life and need a battery cell. It should retain at least 80% health after 500 charge cycles. Ideally it would conform to a non-rectangular cavity inside the device. Thermal management is handled at the pack level, so focus on the cell.

---

## P-208

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We're developing a premium smartphone with all-day battery life and need a battery cell. We need the highest energy density we can get. It should keep surface temperature below 42 degrees C during fast charge. Ideally it would fit in a phone body under 8 mm thick. This is a prototype, so cost is secondary to getting the specs right.

---

## P-209

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're making an industrial-grade impact wrench and need battery cells. Please use NMC-111. They need to deliver sustained high current draw for burst torque. Form factor should use a compact form factor that doesn't unbalance the tool. This is a prototype, so cost is secondary to getting the specs right.

---

## P-210

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a utility-scale renewable integration project. We want something that will last thousands of cycles. The deployment requires cells that operate reliably in an unconditioned outdoor enclosure, and we need to use a standard module form factor for rack mounting. The client is flexible on dimensions but firm on weight.

---

## P-211

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-622 cylindrical battery: 285.6 Ah, grid storage use.

---

## P-212

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete prismatic cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-811 (LiNi0.8Mn0.1Co0.1O2)
>   Cell capacity: 103.3 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 256 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum

---

## P-213

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a tablet for professional use. Main requirement: keep surface temperature below 42 degrees C during fast charge. For form factor, it should weigh under 50 grams for a phone-class cell. Our manufacturing partner has experience with this form factor.

---

## P-214

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Need a cylindrical cell: LFP, around 50 Ah, for consumer electronics application.

---

## P-215

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 pouch cell with the following requirements:
> - Capacity: 2.5 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 213 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: -4 deg C to 41 deg C
> - Target cycle life: 732 cycles

---

## P-216

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a wireless earbud charging case. We need the highest energy density we can get. Performance-wise, it should last a full day of heavy use without recharging. Size-wise, it needs to fit in a phone body under 8 mm thick. We need this design finalized by end of quarter.

---

## P-217

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 4.6 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 206 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum

---

## P-218

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> NMC-111 cylindrical, 270.5 Ah for grid storage. Full design please.

---

## P-219

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our engineering team needs cells for a landscaping leaf blower. A proven, cost-effective cathode chemistry would be ideal. Main concern: charge from dead to full in under an hour. Additionally, be robust enough to survive drops from a 2-meter height. Safety certification is a top priority.

---

## P-220

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a cordless circular saw? We want NMC-811 for maximum energy density. It should run a high-torque drill for at least 45 minutes continuously, and needs to be robust enough to survive drops from a 2-meter height. We may iterate on this, so give us a good starting point.

---

## P-221

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-111 cell, 13.5 Ah, targeting consumer electronics.

---

## P-222

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 111.4 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 172 Wh/kg
>   Temperature range: -20 deg C to 52 deg C
>   Cycle life requirement: 7143 cycles minimum

---

## P-223

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> I need a full parametric design for a NMC-811 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 104.4 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 259 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -20 deg C and 45 deg C
> * Cycle life goal: 1500+
> - Continuous discharge rate: 5.6C
> - Maximum separator thickness: 3.3 microns

**Contradiction:** Using a 3.3 micron separator with 5.6C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-224

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell with the following requirements:
> - Capacity: 13.8 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 296 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 44 deg C
> - Target cycle life: 658 cycles

---

## P-225

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell:
> - Nominal voltage: 3.7 V
> - Application: consumer electronics battery
> - Temperature range: 0 deg C to 40 deg C
> - Cycle life: 500 cycles

---

## P-226

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Need a prismatic cell: NMC-111, around 52.3 Ah, for EV traction application.

**Contradiction:** Operating at -40 deg C with 4.2C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-227

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 cylindrical cell:
> - Nominal voltage: 3.65 V
> - Energy density: at least 227 Wh/kg
> - Application: consumer electronics battery
> - Cycle life: 500 cycles

---

## P-228

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> Specify a NMC-622 cylindrical battery: 8.3 Ah, power tools use.

**Contradiction:** Using a 4.6 micron separator with 5.3C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-229

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our product team needs a battery for a tablet for professional use. Longevity and safety matter more than energy density. The battery must retain at least 80% health after 500 charge cycles, and we need it to conform to a non-rectangular cavity inside the device. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-230

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C6 |

**Prompt:**

> Design a 8.2 Ah NMC-622 prismatic cell for consumer electronics.

**Contradiction:** Requesting 2.41 V nominal voltage with 262.6 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-231

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PR1, PR3 |

**Prompt:**

> Design a NMC-111 prismatic cell with the following requirements:
> - Capacity: 86.7 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 179 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles

**Contradiction:** Requesting 86.7 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-232

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 cylindrical cell with the following requirements:
> - Capacity: 9.1 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 255 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -15 deg C to 54 deg C
> - Target cycle life: 1788 cycles

---

## P-233

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell with the following requirements:
> - Capacity: 14.9 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 290 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: -9 deg C to 43 deg C
> - Target cycle life: 717 cycles

---

## P-234

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a wireless earbud charging case. A proven, cost-effective cathode chemistry would be ideal. Main requirement: support fast charging from 0 to 80% in under 30 minutes. For form factor, it should conform to a non-rectangular cavity inside the device. Budget is not the primary concern here — performance is.

---

## P-235

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a next-generation foldable phone. Please design around NMC-811 chemistry. Main requirement: last a full day of heavy use without recharging. For form factor, it should be as thin as possible for a slim laptop design. We may iterate on this, so give us a good starting point.

---

## P-236

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Looking for a battery cell for a landscaping leaf blower. A mid-range energy density chemistry would work well. Priority is a cell that can handle the vibration and shock of professional job site use. As for size, it should keep total pack weight under 800 grams. Our manufacturing partner has experience with this form factor.

---

## P-237

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a tablet for professional use. We're planning on NMC-111 chemistry. Performance-wise, it should support fast charging from 0 to 80% in under 30 minutes. Size-wise, it needs to fit in a phone body under 8 mm thick. We've already locked in the module architecture, so the cell needs to fit.

---

## P-238

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PR1, PR3 |

**Prompt:**

> Can we get a 80.6 Ah cell that fits in a pocket-sized enclosure? It's for a portable gaming device and portability is everything. We want it as compact as physically possible. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

**Contradiction:** Requesting 80.6 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-239

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell:
> - Capacity: 231.4 Ah
> - Nominal voltage: 3.2 V
> - Energy density: 135 Wh/kg
> - Application: stationary grid energy storage
> - Cycle life: 5000 cycles

---

## P-240

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> Design a NMC-622 prismatic cell with the following requirements:
> - Capacity: 82.6 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 224 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -40 deg C to 45 deg C
> - Target cycle life: 1500 cycles
> - Continuous discharge rate: 4.7C

**Contradiction:** Operating at -40 deg C with 4.7C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-241

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Specify a NMC-811 cylindrical battery: 5.6 Ah, power tools use.

**Contradiction:** Operating at -40 deg C with 4.1C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-242

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're building an electric SUV with 500 km range target and need a battery cell design. We've decided on NMC-111 for the cathode. The cell should deliver consistent power in both highway cruise and stop-and-go driving.use a form factor compatible with CTP (cell-to-pack) architecture

---

## P-243

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-811 cylindrical battery: 118.9 Ah, grid storage use.

---

## P-244

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C6 |

**Prompt:**

> NMC-811 pouch, 4.7 Ah for consumer electronics. Full design please.

**Contradiction:** Requesting 2.43 V nominal voltage with 307.8 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-245

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> We need a cell for a landscaping leaf blower with a nominal voltage around 2.15 V to match our legacy power electronics, but we still want best-in-class energy density — above 235 Wh/kg. Can you design something? We need to hit a specific price point, so don't over-engineer it.

**Contradiction:** Requesting 2.15 V nominal voltage with 235.2 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-246

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Can you spec a cell for a tablet for professional use? We're looking for better-than-average energy density without going too aggressive. It has to keep surface temperature below 42 degrees C during fast charge. Also needs to be as thin as possible for a slim laptop design. This is a prototype, so cost is secondary to getting the specs right.

---

## P-247

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-622 cell, 50 Ah, targeting EV traction.

---

## P-248

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete prismatic cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 100 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 166 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 5000 cycles minimum

---

## P-249

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> NMC-622 prismatic, 112.1 Ah for grid storage. Full design please.

---

## P-250

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C2, C6 |

**Prompt:**

> I need a full parametric design for a LFP cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 8.1 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 247 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

**Contradiction:** LFP chemistry physically cannot achieve 247.4 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-251

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 cylindrical cell with the following requirements:
> - Capacity: 40.4 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 217 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -28 deg C to 49 deg C
> - Target cycle life: 2428 cycles

---

## P-252

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C2, C6 |

**Prompt:**

> We need a battery for a mid-size EV platform for a European OEM that's extremely lightweight and energy-dense — at least 255 Wh/kg. But safety is non-negotiable, so we want to stick with iron phosphate chemistry. Can you make that work? We've already locked in the module architecture, so the cell needs to fit.

**Contradiction:** LFP chemistry physically cannot achieve 255.3 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-253

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're building a long-range electric sedan and need a battery cell design. Use NMC-622 chemistry. The cell should provide reliable range over 400 km on a single charge.use a form factor compatible with CTP (cell-to-pack) architecture Reliability over the full warranty period is essential.

---

## P-254

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Our product team needs a battery for a portable gaming device. We prefer LFP for safety and longevity. The battery must keep surface temperature below 42 degrees C during fast charge, and we need it to weigh under 50 grams for a phone-class cell. Our manufacturing partner has experience with this form factor.

---

## P-255

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for an industrial-grade impact wrench? We prefer LFP for safety and longevity. It should not overheat during continuous heavy-load operation, and needs to use a compact form factor that doesn't unbalance the tool. The R&D team wants to push boundaries on this one.

---

## P-256

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-111 pouch battery cell.
> 
> Requirements:
> * Target capacity: 283.6 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 210 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -11 deg C and 50 deg C
> * Cycle life goal: 8622+

---

## P-257

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 4.1 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 274 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 1000+

---

## P-258

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a laptop that needs to last 12 hours. Use NMC-622 chemistry. Main requirement: keep surface temperature below 42 degrees C during fast charge. For form factor, it should conform to a non-rectangular cavity inside the device. This is a prototype, so cost is secondary to getting the specs right.

---

## P-259

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 pouch cell:
> - Capacity: 10 Ah
> - Nominal voltage: 3.7 V
> - Application: cordless power tool battery
> - Temperature range: -10 deg C to 50 deg C

---

## P-260

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell:
> - Capacity: around 9.1 Ah
> - Nominal voltage: 3.65 V
> - Application: consumer electronics battery

---

## P-261

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a residential solar energy storage system. Gravimetric energy density is our top priority. The deployment requires cells that operate reliably in an unconditioned outdoor enclosure, and we need to minimize cooling requirements for passive thermal management. Budget is not the primary concern here — performance is.

---

## P-262

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> Design a 6.8 Ah NMC-811 prismatic cell for power tools.

**Contradiction:** NMC-811 cycling at -35 deg C with a 8417-cycle life target is contradictory. The high-nickel cathode suffers accelerated capacity fade at low temperatures due to kinetic limitations and SEI growth.

---

## P-263

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our team is working on a mid-size EV platform for a European OEM. Range is everything here — maximize energy per kilogram. We need cells that can deliver consistent power in both highway cruise and stop-and-go driving. be compact enough for a structural battery pack design The client is flexible on dimensions but firm on weight.

---

## P-264

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-811 cell, 127.2 Ah, targeting grid storage.

---

## P-265

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're developing a tablet for professional use and need a battery cell. Please design around NMC-811 chemistry. It should last a full day of heavy use without recharging. Ideally it would conform to a non-rectangular cavity inside the device. We need this design finalized by end of quarter.

---

## P-266

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a premium smartphone with all-day battery life. We're looking for better-than-average energy density without going too aggressive. Main requirement: deliver stable voltage throughout the discharge curve. For form factor, it should fit in a phone body under 8 mm thick. The customer has asked for a conservative design.

---

## P-267

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 3.8 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 140 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum

---

## P-268

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a residential solar energy storage system. We want iron phosphate for this application. The deployment requires cells that tolerate extended float-charge periods without calendar aging issues, and we need to prioritize cost per kWh over weight or volume. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-269

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 97.8 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 159 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum

---

## P-270

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Design a 15 Ah NMC-622 pouch cell for consumer electronics.

---

## P-271

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Need a prismatic cell: LFP, around 50 Ah, for consumer electronics application.

---

## P-272

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a professional cordless drill. The cell must not overheat during continuous heavy-load operation. It also has to be robust enough to survive drops from a 2-meter height. We need this design finalized by end of quarter.

---

## P-273

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> I need a full parametric design for a NMC-111 pouch battery cell.
> 
> Requirements:
> * Target capacity: 100 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 193 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -40 deg C and 50 deg C
> * Cycle life goal: 5000+
> - Continuous discharge rate: 3.5C

**Contradiction:** Operating at -40 deg C with 3.5C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-274

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | PO5, PO7 |

**Prompt:**

> Generate parameters for a pouch NMC-622 cell, 141.2 Ah, targeting EV traction.

**Contradiction:** A 141.2 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-275

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-111 pouch battery: 100 Ah, grid storage use.

---

## P-276

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> We need a cell for a backup power system for a data center with a nominal voltage around 2.23 V to match our legacy power electronics, but we still want best-in-class energy density — above 268 Wh/kg. Can you design something? Reliability over the full warranty period is essential.

**Contradiction:** Requesting 2.23 V nominal voltage with 268.5 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-277

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C6 |

**Prompt:**

> Design a 10 Ah NMC-111 prismatic cell for power tools.

**Contradiction:** Requesting 2.29 V nominal voltage with 230.5 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-278

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> Please generate a complete prismatic cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 216.2 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 157 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 5000 cycles minimum
> - Continuous discharge rate: 5.6C
> - Maximum separator thickness: 3.8 microns

**Contradiction:** Using a 3.8 micron separator with 5.6C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-279

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for a commercial electric delivery van. We want something that will last thousands of cycles. Key priorities: the cell must support regenerative braking at moderate C-rates, and not exceed 250 kg for the full module. We need to hit a specific price point, so don't over-engineer it.

---

## P-280

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> Specify a NMC-622 prismatic battery: 58.2 Ah, EV traction use.

**Contradiction:** Requesting 247.8 Wh/kg energy density with 5.9C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-281

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for an electric SUV with 500 km range target. Key priorities: the cell must maintain at least 80% capacity after 1500 full cycles, and fit within a standard skateboard platform. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-282

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 pouch cell:
> - Nominal voltage: 3.65 V
> - Energy density: at least 213 Wh/kg
> - Application: electric vehicle traction battery
> - Cycle life: 1500 cycles

---

## P-283

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell with the following requirements:
> - Capacity: 10.3 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 272 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 40 deg C
> - Target cycle life: 500 cycles

---

## P-284

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell:
> - Capacity: approximately 10 Ah
> - Nominal voltage: 3.7 V
> - Application: cordless power tool battery
> - Cycle life: 1000 cycles

---

## P-285

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell with the following requirements:
> - Capacity: 2.6 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 295 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -16 deg C to 55 deg C
> - Target cycle life: 1366 cycles

---

## P-286

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Generate parameters for a pouch NMC-811 cell, 5.4 Ah, targeting power tools.

**Contradiction:** Operating at -40 deg C with 3.6C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-287

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PR1, PR3 |

**Prompt:**

> We need 157.0 Ah of capacity in the smallest possible package for a residential solar energy storage system. Think credit-card-sized if possible. The device has very limited internal volume. Reliability over the full warranty period is essential.

**Contradiction:** Requesting 157.0 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-288

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 288.3 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 249 Wh/kg
>   Temperature range: -13 deg C to 55 deg C
>   Cycle life requirement: 8370 cycles minimum

---

## P-289

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We've been asked to source cells for a grid-scale frequency regulation unit. We want a good balance of cost, safety, and performance. They have to deliver consistent round-trip efficiency above 92%. Cost-wise we want to minimize cooling requirements for passive thermal management. Safety certification is a top priority.

---

## P-290

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 pouch battery cell.
> 
> Requirements:
> * Target capacity: 277.4 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 293 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -14 deg C and 55 deg C
> * Cycle life goal: 6567+

---

## P-291

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C4 |

**Prompt:**

> Our application is an industrial-grade impact wrench that operates in Arctic conditions — we need reliable performance down to -40 deg C. It also needs to accept fast charging at 3.8C when plugged in at a remote charging station. Is that feasible? Our manufacturing partner has experience with this form factor.

**Contradiction:** Operating at -40 deg C with 3.8C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-292

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> Please generate a complete cylindrical cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 69.4 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 150 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum
> - Continuous discharge rate: 5.1C
> - Maximum separator thickness: 5.0 microns

**Contradiction:** Using a 5.0 micron separator with 5.1C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-293

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 8.1 Ah NMC-811 pouch cell for power tools.

---

## P-294

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell with the following requirements:
> - Capacity: 4.7 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 239 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 40 deg C
> - Target cycle life: 500 cycles

---

## P-295

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Can you help design a cell for an urban electric bus with daily fast-charge cycles? Safety and thermal stability are paramount. It needs to deliver consistent power in both highway cruise and stop-and-go driving. We'd like it to fit within a standard skateboard platform. We need this design finalized by end of quarter.

---

## P-296

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PO5, PO7 |

**Prompt:**

> We need a high-capacity pouch cell — around 151.1 Ah — but the packaging needs to be as slim as possible for a contractor's reciprocating saw used on job sites. Can we minimize the edge sealing area to under a millimeter? We need to hit a specific price point, so don't over-engineer it.

**Contradiction:** A 151.1 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-297

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 2.8 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 295 Wh/kg
> * End use: consumer electronics battery
> * Must operate between -1 deg C and 42 deg C
> * Cycle life goal: 824+

---

## P-298

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a professional cordless drill? Please use NMC-111. It should charge from dead to full in under an hour, and needs to keep total pack weight under 800 grams. Budget is not the primary concern here — performance is.

---

## P-299

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell with the following requirements:
> - Capacity: 5.5 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 157 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 40 deg C
> - Target cycle life: 500 cycles

---

## P-300

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> Specify a NMC-111 pouch battery: 100 Ah, grid storage use. [Design variant 96]

**Contradiction:** Using a 3.3 micron separator with 5.4C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-301

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP cylindrical cell:
> - Capacity: 233.7 Ah (nominal)
> - Nominal voltage: 3.2 V
> - Energy density: 141 Wh/kg
> - Application: stationary grid energy storage

---

## P-302

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-111 pouch battery cell.
> 
> Requirements:
> * Target capacity: 50.7 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 214 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -28 deg C and 47 deg C
> * Cycle life goal: 1991+

---

## P-303

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a residential solar energy storage system. The cathode should be NMC-622. The deployment requires cells that last at least 10 years of daily cycling, and we need to prioritize cost per kWh over weight or volume. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-304

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 2.2 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 217 Wh/kg
>   Temperature range: -8 deg C to 45 deg C
>   Cycle life requirement: 835 cycles minimum

---

## P-305

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 50 Ah NMC-811 cylindrical cell for consumer electronics.

---

## P-306

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a cylindrical NMC-622 cell, 50 Ah, targeting EV traction.

---

## P-307

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Need a prismatic cell: LFP, around 83.6 Ah, for EV traction application.

**Contradiction:** Operating at -40 deg C with 3.4C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-308

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> We need a cell for an urban electric bus with daily fast-charge cycles with a nominal voltage around 2.5 V to match our legacy power electronics, but we still want best-in-class energy density — above 251 Wh/kg. Can you design something? We need this design finalized by end of quarter.

**Contradiction:** Requesting 2.5 V nominal voltage with 251.8 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-309

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-111 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 138.7 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 209 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -23 deg C and 49 deg C
> * Cycle life goal: 2209+

---

## P-310

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP cylindrical cell:
> - Nominal voltage: 3.2 V
> - Energy density: 166 watt-hours per kilogram
> - Application: consumer electronics battery

---

## P-311

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO5, PO7 |

**Prompt:**

> Design a NMC-811 pouch cell with the following requirements:
> - Capacity: 171.2 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 238 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles
> - Maximum edge seal width: 0.5 mm

**Contradiction:** A 171.2 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-312

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Need a cylindrical cell: NMC-622, around 50 Ah, for power tools application.

---

## P-313

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | PO1, PO5 |

**Prompt:**

> Specify a NMC-622 pouch battery: 87.5 Ah, consumer electronics use.

**Contradiction:** Requesting 87.5 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-314

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PR1, PR3 |

**Prompt:**

> I need a full parametric design for a NMC-622 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 127.2 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 236 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

**Contradiction:** Requesting 127.2 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-315

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a laptop that needs to last 12 hours. We want NMC-811 for maximum energy density. Main requirement: deliver stable voltage throughout the discharge curve. For form factor, it should fit in a phone body under 8 mm thick. The R&D team wants to push boundaries on this one.

---

## P-316

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a portable gaming device. We're going with NMC-622. Main requirement: retain at least 80% health after 500 charge cycles. For form factor, it should conform to a non-rectangular cavity inside the device.

---

## P-317

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | CY1, CY5 |

**Prompt:**

> Specify a NMC-111 cylindrical battery: 80.2 Ah, consumer electronics use.

**Contradiction:** Requesting 80.2 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-318

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 cylindrical cell:
> - Capacity: 114 Ah
> - Nominal voltage: 3.65 V
> - Energy density: at least 211 Wh/kg
> - Application: stationary grid energy storage

---

## P-319

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 4.8 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 167 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum

---

## P-320

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell:
> - Nominal voltage: 3.65 V
> - Energy density: 262 Wh/kg
> - Application: consumer electronics battery
> - Cycle life: 500 cycles

---

## P-321

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C4 |

**Prompt:**

> We're deploying a cordless circular saw in northern Canada where temperatures regularly drop to -40 deg C. The vehicles still need to fast-charge at 3.4C at those temperatures. What cell design would work here?

**Contradiction:** Operating at -40 deg C with 3.4C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-322

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C6 |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 9.2 Ah
> * Nominal voltage: 2.1 V
> * Energy density: at least 344 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

**Contradiction:** Requesting 2.1 V nominal voltage with 344.8 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-323

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 2.2 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 256 Wh/kg
>   Temperature range: -5 deg C to 40 deg C
>   Cycle life requirement: 660 cycles minimum

---

## P-324

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Can you spec a cell for a laptop that needs to last 12 hours? Longevity and safety matter more than energy density. It has to retain at least 80% health after 500 charge cycles. Also needs to weigh under 50 grams for a phone-class cell. Safety certification is a top priority.

---

## P-325

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a contractor's reciprocating saw used on job sites? The cathode should be NMC-622. It should charge from dead to full in under an hour, and needs to keep total pack weight under 800 grams. The client is flexible on dimensions but firm on weight.

---

## P-326

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C4, C1 |

**Prompt:**

> Our application is a landscaping leaf blower that operates in Arctic conditions — we need reliable performance down to -10 deg C. It also needs to accept fast charging at 5.3C when plugged in at a remote charging station. Is that feasible? This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

**Contradiction:** Using a 4.6 micron separator with 5.3C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-327

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C6 |

**Prompt:**

> Design a NMC-622 pouch cell with the following requirements:
> - Capacity: 6.2 Ah
> - Nominal voltage: 2.19 V
> - Target energy density: 273 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 1000 cycles

**Contradiction:** Requesting 2.19 V nominal voltage with 273.1 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-328

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C2 |

**Prompt:**

> Please generate a complete prismatic cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-811 (LiNi0.8Mn0.1Co0.1O2)
>   Cell capacity: 119.6 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 331 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 5000 cycles minimum
> - Continuous discharge rate: 4.1C

**Contradiction:** Requesting 331.7 Wh/kg energy density with 4.1C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-329

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell with the following requirements:
> - Capacity: 6.1 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 232 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 1000 cycles

---

## P-330

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a commercial peak-shaving installation and need cells that can tolerate extended float-charge periods without calendar aging issues. We're going with NMC-622. For the installation, we want to be designed for easy field replacement of individual cells. Budget is not the primary concern here — performance is.

---

## P-331

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 106.8 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 211 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 5000 cycles minimum

---

## P-332

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> We need a cell for a portable gaming device with a nominal voltage around 2.28 V to match our legacy power electronics, but we still want best-in-class energy density — above 318 Wh/kg. Can you design something? We need this design finalized by end of quarter.

**Contradiction:** Requesting 2.28 V nominal voltage with 318.8 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-333

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | CY1, CY5 |

**Prompt:**

> We want to use standard 18650 cells for a wireless earbud charging case to keep costs down, but we need at least 80.1 Ah per cell. Our pack design is optimized for that form factor. Can it be done? Our manufacturing partner has experience with this form factor.

**Contradiction:** Requesting 80.1 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-334

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell:
> - Capacity: 3.6 Ah
> - Nominal voltage: 3.65 V
> - Application: cordless power tool battery
> - Temperature range: -10 deg C to 50 deg C

---

## P-335

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 pouch cell with the following requirements:
> - Capacity: 57.1 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 224 Wh/kg
> - Application: electric vehicle traction battery
> - Operating temperature: -20 deg C to 45 deg C
> - Target cycle life: 1500 cycles

---

## P-336

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our product team needs a battery for a tablet for professional use. Safety and thermal stability are paramount. The battery must retain at least 80% health after 500 charge cycles, and we need it to weigh under 50 grams for a phone-class cell. Thermal management is handled at the pack level, so focus on the cell.

---

## P-337

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 cylindrical cell:
> - Capacity: 114.3 Ah (nominal)
> - Nominal voltage: 3.65 V
> - Energy density: at least 282 Wh/kg
> - Application: electric vehicle traction battery
> - Cycle life: 1500 cycles

---

## P-338

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a heavy-duty angle grinder for metalwork. Range is everything here — maximize energy per kilogram. The cell must deliver sustained high current draw for burst torque. It also has to use a compact form factor that doesn't unbalance the tool.

---

## P-339

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our client wants a grid-scale frequency regulation unit. A proven, cost-effective cathode chemistry would be ideal. The cells need to last at least 10 years of daily cycling. We'd prefer to use a standard module form factor for rack mounting. We need to hit a specific price point, so don't over-engineer it.

---

## P-340

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell:
> - Nominal voltage: 3.65 V
> - Energy density: 278 watt-hours per kilogram
> - Application: cordless power tool battery

---

## P-341

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO1, PO5 |

**Prompt:**

> Design a LFP pouch cell with the following requirements:
> - Capacity: 166.4 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 144 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles

**Contradiction:** Requesting 166.4 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-342

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Need a cylindrical cell: NMC-622, around 108.6 Ah, for grid storage application.

---

## P-343

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for an urban electric bus with daily fast-charge cycles and we need a complete cell spec. We're going with NMC-622. The cell has to handle DC fast charging at up to 2C without excessive degradation. Also, it should not exceed 250 kg for the full module. The customer has asked for a conservative design.

---

## P-344

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PO1, PO5 |

**Prompt:**

> Please generate a complete pouch cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 100.4 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 204 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum

**Contradiction:** Requesting 100.4 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-345

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | PR1, PR3 |

**Prompt:**

> Need a prismatic cell: NMC-622, around 91.2 Ah, for power tools application.

**Contradiction:** Requesting 91.2 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-346

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP pouch cell:
> - Capacity: 8.3 Ah
> - Nominal voltage: 3.2 V
> - Application: cordless power tool battery
> - Cycle life: 1000 cycles

---

## P-347

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete prismatic cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 2.3 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 172 Wh/kg
>   Temperature range: -8 deg C to 42 deg C
>   Cycle life requirement: 815 cycles minimum

---

## P-348

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 60.6 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 166 Wh/kg
>   Temperature range: -20 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum

---

## P-349

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | PR1, PR3 |

**Prompt:**

> I need a full parametric design for a NMC-811 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 178.9 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 236 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

**Contradiction:** Requesting 178.9 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-350

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a grid-scale frequency regulation unit and need cells that can deliver consistent round-trip efficiency above 92%. We've selected NMC-811. For the installation, we want to be designed for easy field replacement of individual cells. Safety certification is a top priority.

---

## P-351

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We're making a cordless circular saw and need battery cells. A mid-range energy density chemistry would work well. They need to charge from dead to full in under an hour. Form factor should use a compact form factor that doesn't unbalance the tool. We may iterate on this, so give us a good starting point.

---

## P-352

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> Our system operates at 2.33 V per cell. For a wireless earbud charging case, we also need at least 213 Wh/kg. We can't change the voltage — the BMS firmware is locked to that range. We may iterate on this, so give us a good starting point.

**Contradiction:** Requesting 2.33 V nominal voltage with 213.3 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-353

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Can you spec a cell for a tablet for professional use? It has to last a full day of heavy use without recharging. Also needs to conform to a non-rectangular cavity inside the device.

---

## P-354

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-811 pouch battery: 50 Ah, consumer electronics use.

---

## P-355

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for an industrial-grade impact wrench? We've selected NMC-811. It should run a high-torque drill for at least 45 minutes continuously, and needs to be robust enough to survive drops from a 2-meter height.

---

## P-356

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: LFP (LiFePO4)
>   Cell capacity: 150.4 Ah
>   Voltage: 3.2 V nominal
>   Energy density target: 152 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 5000 cycles minimum

---

## P-357

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a backup power system for a data center and need cells that can handle 5000+ deep discharge cycles without significant degradation. Range is everything here — maximize energy per kilogram. For the installation, we want to use a standard module form factor for rack mounting. We're on a tight timeline for this.

---

## P-358

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I'm working on a backup power system for a data center. Please use LFP chemistry. Key requirement: deliver consistent round-trip efficiency above 92%. The cells should be designed for easy field replacement of individual cells. We've already locked in the module architecture, so the cell needs to fit.

---

## P-359

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our client wants a residential solar energy storage system. We want something that will last thousands of cycles. The cells need to deliver consistent round-trip efficiency above 92%. We'd prefer to minimize cooling requirements for passive thermal management.

---

## P-360

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you spec a cell for a next-generation foldable phone? Use NMC-622 chemistry. It has to last a full day of heavy use without recharging. Also needs to weigh under 50 grams for a phone-class cell. The R&D team wants to push boundaries on this one.

---

## P-361

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our team is working on a high-performance electric sports car. We need the highest energy density we can get. We need cells that can deliver consistent power in both highway cruise and stop-and-go driving. use a form factor compatible with CTP (cell-to-pack) architecture Reliability over the full warranty period is essential.

---

## P-362

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-811 pouch battery: 50 Ah, EV traction use.

---

## P-363

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our team is working on a commercial electric delivery van. Range is everything here — maximize energy per kilogram. We need cells that can maintain at least 80% capacity after 1500 full cycles. be compact enough for a structural battery pack design We're on a tight timeline for this.

---

## P-364

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 6.9 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 207 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum

---

## P-365

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for a commercial electric delivery van. Key priorities: the cell must handle DC fast charging at up to 2C without excessive degradation, and use a form factor compatible with CTP (cell-to-pack) architecture.

---

## P-366

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | CY1, CY5 |

**Prompt:**

> Specify a LFP cylindrical battery: 89 Ah, EV traction use.

**Contradiction:** Requesting 89.0 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-367

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 50 Ah NMC-622 pouch cell for power tools.

---

## P-368

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> Our system operates at 2.13 V per cell. For an urban electric bus with daily fast-charge cycles, we also need at least 247 Wh/kg. We can't change the voltage — the BMS firmware is locked to that range. Safety certification is a top priority.

**Contradiction:** Requesting 2.13 V nominal voltage with 247.4 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-369

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C4, C1 |

**Prompt:**

> We're deploying a utility-scale renewable integration project in northern Canada where temperatures regularly drop to -10 deg C. The vehicles still need to fast-charge at 4.4C at those temperatures. What cell design would work here? We're on a tight timeline for this.

**Contradiction:** Using a 3.6 micron separator with 4.4C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-370

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our product team needs a battery for a tablet for professional use. The cathode should be NMC-622. The battery must last a full day of heavy use without recharging, and we need it to conform to a non-rectangular cavity inside the device. We need to hit a specific price point, so don't over-engineer it.

---

## P-371

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our team is working on a long-range electric sedan. We need cells that can support regenerative braking at moderate C-rates. be compact enough for a structural battery pack design The client is flexible on dimensions but firm on weight.

---

## P-372

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 7.1 Ah LFP prismatic cell for power tools.

---

## P-373

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C6 |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 7 Ah
> * Nominal voltage: 2.11 V
> * Energy density: at least 328 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 1000+

**Contradiction:** Requesting 2.11 V nominal voltage with 328.6 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-374

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP cylindrical cell:
> - Capacity: 6.7 Ah (nominal)
> - Nominal voltage: 3.2 V
> - Application: cordless power tool battery

---

## P-375

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our engineering team needs cells for a heavy-duty angle grinder for metalwork. Gravimetric energy density is our top priority. Main concern: deliver sustained high current draw for burst torque. Additionally, fit the standard battery bay of our existing tool platform. We may iterate on this, so give us a good starting point.

---

## P-376

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> NMC-622 pouch, 10.4 Ah for consumer electronics. Full design please.

---

## P-377

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-111 cylindrical battery: 50 Ah, power tools use.

---

## P-378

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a tablet for professional use. Use NMC-622 chemistry. Main requirement: keep surface temperature below 42 degrees C during fast charge. For form factor, it should conform to a non-rectangular cavity inside the device. Budget is not the primary concern here — performance is.

---

## P-379

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 50 Ah NMC-111 pouch cell for EV traction.

---

## P-380

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 5.8 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 246 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 1000+

---

## P-381

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're building an electric SUV with 500 km range target and need a battery cell design. We want something that will last thousands of cycles. The cell should support regenerative braking at moderate C-rates.be compact enough for a structural battery pack design Thermal management is handled at the pack level, so focus on the cell.

---

## P-382

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Design a 7.6 Ah NMC-811 prismatic cell for consumer electronics.

**Contradiction:** Operating at -40 deg C with 3.7C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-383

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our client wants a commercial peak-shaving installation. We're looking for better-than-average energy density without going too aggressive. The cells need to operate reliably in an unconditioned outdoor enclosure. We'd prefer to minimize cooling requirements for passive thermal management. We're on a tight timeline for this.

---

## P-384

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Need a cylindrical cell: NMC-622, around 2.8 Ah, for consumer electronics application.

---

## P-385

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our client wants a commercial peak-shaving installation. Please use NMC-111. The cells need to deliver consistent round-trip efficiency above 92%. We'd prefer to prioritize cost per kWh over weight or volume. The client is flexible on dimensions but firm on weight.

---

## P-386

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell:
> - Nominal voltage: 3.7 V
> - Energy density: at least 164 Wh/kg
> - Application: stationary grid energy storage
> - Temperature range: -10 deg C to 50 deg C

---

## P-387

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | PO5, PO7 |

**Prompt:**

> We need a high-capacity pouch cell — around 110.8 Ah — but the packaging needs to be as slim as possible for a microgrid for an off-grid community. Can we minimize the edge sealing area to under a millimeter? We're on a tight timeline for this.

**Contradiction:** A 110.8 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-388

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you spec a cell for a next-generation foldable phone? Safety and thermal stability are paramount. It has to support fast charging from 0 to 80% in under 30 minutes. Also needs to weigh under 50 grams for a phone-class cell.

---

## P-389

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're building a mid-size EV platform for a European OEM and need a battery cell design. We're going with NMC-622. The cell should support regenerative braking at moderate C-rates.fit within a standard skateboard platform Our manufacturing partner has experience with this form factor.

---

## P-390

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-111 cylindrical battery: 11.6 Ah, consumer electronics use.

---

## P-391

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 pouch cell:
> - Nominal voltage: 3.65 V
> - Application: cordless power tool battery
> - Temperature range: -10 deg C to 50 deg C

---

## P-392

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C2, C6 |

**Prompt:**

> Design a 248.8 Ah LFP cylindrical cell for grid storage.

**Contradiction:** LFP chemistry physically cannot achieve 220.4 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-393

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 9.1 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 254 Wh/kg
>   Temperature range: -20 deg C to 51 deg C
>   Cycle life requirement: 1528 cycles minimum

---

## P-394

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete pouch cell design for consumer electronics battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 2.1 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 255 Wh/kg
>   Temperature range: -4 deg C to 42 deg C
>   Cycle life requirement: 850 cycles minimum

---

## P-395

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-111 pouch battery: 102.3 Ah, grid storage use.

---

## P-396

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Our product team needs a battery for a next-generation foldable phone. We're looking for better-than-average energy density without going too aggressive. The battery must last a full day of heavy use without recharging, and we need it to be as thin as possible for a slim laptop design. We're on a tight timeline for this.

---

## P-397

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Our team is working on a long-range electric sedan. We're looking for better-than-average energy density without going too aggressive. We need cells that can handle DC fast charging at up to 2C without excessive degradation. fit within a standard skateboard platform We're on a tight timeline for this.

---

## P-398

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> Our system operates at 2.31 V per cell. For a contractor's reciprocating saw used on job sites, we also need at least 269 Wh/kg. We can't change the voltage — the BMS firmware is locked to that range.

**Contradiction:** Requesting 2.31 V nominal voltage with 269.8 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-399

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C2 |

**Prompt:**

> NMC-811 prismatic, 107.2 Ah for EV traction. Full design please.

**Contradiction:** NMC-811 cycling at -35 deg C with a 6535-cycle life target is contradictory. The high-nickel cathode suffers accelerated capacity fade at low temperatures due to kinetic limitations and SEI growth.

---

## P-400

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 pouch cell:
> - Nominal voltage: 3.65 V
> - Energy density: at least 201 Wh/kg
> - Application: stationary grid energy storage
> - Temperature range: -10 deg C to 50 deg C

---

## P-401

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a microgrid for an off-grid community. Range is everything here — maximize energy per kilogram. The deployment requires cells that tolerate extended float-charge periods without calendar aging issues, and we need to use a standard module form factor for rack mounting. We need to hit a specific price point, so don't over-engineer it.

---

## P-402

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We've been asked to source cells for a commercial peak-shaving installation. We prefer LFP for safety and longevity. They have to tolerate extended float-charge periods without calendar aging issues. Cost-wise we want to prioritize cost per kWh over weight or volume. Reliability over the full warranty period is essential.

---

## P-403

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-111 cell, 9.9 Ah, targeting power tools.

---

## P-404

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> LFP prismatic, 50 Ah for EV traction. Full design please.

---

## P-405

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We're building a long-range electric sedan and need a battery cell design. We're looking for better-than-average energy density without going too aggressive. The cell should deliver consistent power in both highway cruise and stop-and-go driving.be compact enough for a structural battery pack design We need this design finalized by end of quarter.

---

## P-406

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell:
> - Capacity: approximately 98.2 Ah
> - Nominal voltage: 3.2 V
> - Application: electric vehicle traction battery

---

## P-407

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | CY1, CY5 |

**Prompt:**

> Need a cylindrical cell: NMC-622, around 72.7 Ah, for EV traction application.

**Contradiction:** Requesting 72.7 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-408

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | PO5, PO7 |

**Prompt:**

> Specify a LFP pouch battery: 145.3 Ah, EV traction use.

**Contradiction:** A 145.3 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-409

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 prismatic cell with the following requirements:
> - Capacity: 107.1 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 293 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -18 deg C to 54 deg C
> - Target cycle life: 7434 cycles

---

## P-410

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for an industrial-grade impact wrench. We want NMC-811 for maximum energy density. The cell must deliver sustained high current draw for burst torque. It also has to use a compact form factor that doesn't unbalance the tool. We need to hit a specific price point, so don't over-engineer it.

---

## P-411

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We've got a project for a mid-size EV platform for a European OEM and we need a complete cell spec. We're looking for better-than-average energy density without going too aggressive. The cell has to handle DC fast charging at up to 2C without excessive degradation. Also, it should be compact enough for a structural battery pack design. Reliability over the full warranty period is essential.

---

## P-412

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C2 |

**Prompt:**

> We're designing a heavy-duty angle grinder for metalwork that needs maximum range but also needs to handle very fast charging — at least 5.6C continuous. Energy density should be above 340 Wh/kg. Weight is absolutely critical. Budget is not the primary concern here — performance is.

**Contradiction:** Requesting 340.5 Wh/kg energy density with 5.6C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-413

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a microgrid for an off-grid community. A mid-range energy density chemistry would work well. The deployment requires cells that handle 5000+ deep discharge cycles without significant degradation, and we need to minimize cooling requirements for passive thermal management. We need to hit a specific price point, so don't over-engineer it.

---

## P-414

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> I need a full parametric design for a LFP pouch battery cell.
> 
> Requirements:
> * Target capacity: 91.9 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 136 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -40 deg C and 45 deg C
> * Cycle life goal: 1500+
> - Continuous discharge rate: 4.4C

**Contradiction:** Operating at -40 deg C with 4.4C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-415

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> I need a full parametric design for a NMC-622 pouch battery cell.
> 
> Requirements:
> * Target capacity: 107.6 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 229 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+
> - Continuous discharge rate: 5.4C
> - Maximum separator thickness: 4.9 microns

**Contradiction:** Using a 4.9 micron separator with 5.4C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-416

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I'm working on a microgrid for an off-grid community. Key requirement: handle 5000+ deep discharge cycles without significant degradation. The cells should use a standard module form factor for rack mounting. We need to hit a specific price point, so don't over-engineer it.

---

## P-417

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a LFP prismatic cell:
> - Capacity: 7 Ah (nominal)
> - Nominal voltage: 3.2 V
> - Application: cordless power tool battery

---

## P-418

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell with the following requirements:
> - Capacity: 10 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 180 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 1000 cycles

---

## P-419

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 48.3 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 289 Wh/kg
> * End use: electric vehicle traction battery
> * Must operate between -24 deg C and 46 deg C
> * Cycle life goal: 2579+

---

## P-420

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for a high-performance electric sports car. Key priorities: the cell must provide reliable range over 400 km on a single charge, and not exceed 250 kg for the full module. We've already locked in the module architecture, so the cell needs to fit.

---

## P-421

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> Design a LFP cylindrical cell with the following requirements:
> - Capacity: 201.3 Ah
> - Nominal voltage: 3.2 V
> - Target energy density: 160 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -40 deg C to 50 deg C
> - Target cycle life: 5000 cycles
> - Continuous discharge rate: 4.4C

**Contradiction:** Operating at -40 deg C with 4.4C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-422

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 11.8 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 254 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

---

## P-423

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-111 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 2.4 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 209 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -19 deg C and 53 deg C
> * Cycle life goal: 1714+

---

## P-424

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a cordless circular saw. Range is everything here — maximize energy per kilogram. The cell must charge from dead to full in under an hour. It also has to fit the standard battery bay of our existing tool platform.

---

## P-425

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We've been asked to source cells for a residential solar energy storage system. We need the highest energy density we can get. They have to deliver consistent round-trip efficiency above 92%. Cost-wise we want to minimize cooling requirements for passive thermal management. Budget is not the primary concern here — performance is.

---

## P-426

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-111 pouch battery cell.
> 
> Requirements:
> * Target capacity: 10 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 174 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 1000+

---

## P-427

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a LFP pouch battery cell.
> 
> Requirements:
> * Target capacity: 11.9 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 133 Wh/kg
> * End use: consumer electronics battery
> * Must operate between 0 deg C and 40 deg C
> * Cycle life goal: 500+

---

## P-428

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell with the following requirements:
> - Capacity: 2.7 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 214 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -17 deg C to 54 deg C
> - Target cycle life: 1575 cycles

---

## P-429

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Need a pouch cell: LFP, around 9.3 Ah, for power tools application.

---

## P-430

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 cylindrical cell:
> - Capacity: around 6.2 Ah
> - Nominal voltage: 3.65 V
> - Energy density: at least 200 Wh/kg
> - Application: cordless power tool battery
> - Temperature range: -10 deg C to 50 deg C

---

## P-431

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a pouch NMC-111 cell, 50 Ah, targeting consumer electronics.

---

## P-432

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-811 (LiNi0.8Mn0.1Co0.1O2)
>   Cell capacity: 49.9 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 293 Wh/kg
>   Temperature range: -20 deg C to 50 deg C
>   Cycle life requirement: 2614 cycles minimum

---

## P-433

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 pouch battery cell.
> 
> Requirements:
> * Target capacity: 8 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 281 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 1000+

---

## P-434

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 pouch cell:
> - Capacity: 100 Ah
> - Nominal voltage: 3.7 V
> - Energy density: at least 165 Wh/kg
> - Application: stationary grid energy storage
> - Cycle life: 5000 cycles

---

## P-435

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a commercial peak-shaving installation and need cells that can tolerate extended float-charge periods without calendar aging issues. We're looking for better-than-average energy density without going too aggressive. For the installation, we want to prioritize cost per kWh over weight or volume. This is a prototype, so cost is secondary to getting the specs right.

---

## P-436

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C6 |

**Prompt:**

> NMC-622 cylindrical, 11.1 Ah for consumer electronics. Full design please.

**Contradiction:** Requesting 2.37 V nominal voltage with 292.7 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-437

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We're developing a premium smartphone with all-day battery life and need a battery cell. Range is everything here — maximize energy per kilogram. It should last a full day of heavy use without recharging. Ideally it would weigh under 50 grams for a phone-class cell.

---

## P-438

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Our engineering team needs cells for a professional cordless drill. Safety and thermal stability are paramount. Main concern: charge from dead to full in under an hour. Additionally, keep total pack weight under 800 grams.

---

## P-439

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> We're developing a tablet for professional use and need a battery cell. A proven, cost-effective cathode chemistry would be ideal. It should retain at least 80% health after 500 charge cycles. Ideally it would fit in a phone body under 8 mm thick. The R&D team wants to push boundaries on this one.

---

## P-440

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell:
> - Capacity: approximately 121.4 Ah
> - Nominal voltage: 3.65 V
> - Application: stationary grid energy storage
> - Cycle life: 5000 cycles

---

## P-441

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Generate parameters for a prismatic NMC-811 cell, 9.8 Ah, targeting power tools.

---

## P-442

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> I need a full parametric design for a NMC-111 cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 12.7 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 187 Wh/kg
> * End use: consumer electronics battery
> * Must operate between -40 deg C and 40 deg C
> * Cycle life goal: 500+

**Contradiction:** Operating at -40 deg C with 3.0C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-443

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Looking for a battery cell for an industrial-grade impact wrench. Please use LFP chemistry. Priority is a cell that can run a high-torque drill for at least 45 minutes continuously. As for size, it should fit the standard battery bay of our existing tool platform. This is a prototype, so cost is secondary to getting the specs right.

---

## P-444

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're developing a wireless earbud charging case and need a battery cell. We prefer LFP for safety and longevity. It should keep surface temperature below 42 degrees C during fast charge. Ideally it would fit in a phone body under 8 mm thick. Safety certification is a top priority.

---

## P-445

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C2, C6 |

**Prompt:**

> I need a cell for an urban electric bus with daily fast-charge cycles with the safety profile of LFP but the energy density of a high-nickel cell — something around 235 Wh/kg. What can you come up with? We may iterate on this, so give us a good starting point.

**Contradiction:** LFP chemistry physically cannot achieve 235.0 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-446

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I'm working on a microgrid for an off-grid community. A mid-range energy density chemistry would work well. Key requirement: tolerate extended float-charge periods without calendar aging issues. The cells should use a standard module form factor for rack mounting. We need to hit a specific price point, so don't over-engineer it.

---

## P-447

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for an electric SUV with 500 km range target. Please use LFP chemistry. Key priorities: the cell must maintain at least 80% capacity after 1500 full cycles, and be compact enough for a structural battery pack design. The customer has asked for a conservative design.

---

## P-448

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C2 |

**Prompt:**

> Please generate a complete pouch cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-811 (LiNi0.8Mn0.1Co0.1O2)
>   Cell capacity: 6.2 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 244 Wh/kg
>   Temperature range: -35 deg C to 50 deg C
>   Cycle life requirement: 9447 cycles minimum

**Contradiction:** NMC-811 cycling at -35 deg C with a 9447-cycle life target is contradictory. The high-nickel cathode suffers accelerated capacity fade at low temperatures due to kinetic limitations and SEI growth.

---

## P-449

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Design a 7.9 Ah LFP cylindrical cell for power tools.

**Contradiction:** Operating at -40 deg C with 4.3C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-450

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-811 prismatic battery cell.
> 
> Requirements:
> * Target capacity: 136.8 Ah
> * Nominal voltage: 3.65 V
> * Energy density: at least 276 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+

---

## P-451

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're building a mid-size EV platform for a European OEM and need a battery cell design. We need the highest energy density we can get. The cell should maintain at least 80% capacity after 1500 full cycles.be compact enough for a structural battery pack design This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-452

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> Can you help design a cell for a commercial electric delivery van? Safety and thermal stability are paramount. It needs to support regenerative braking at moderate C-rates. We'd like it to fit within a standard skateboard platform. We may iterate on this, so give us a good starting point.

---

## P-453

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | PR1, PR3 |

**Prompt:**

> Need a prismatic cell: LFP, around 148 Ah, for consumer electronics application.

**Contradiction:** Requesting 148.0 Ah in a very compact form factor is volumetrically impossible. The required electrode area cannot fit within the specified dimensions.

---

## P-454

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for an industrial-grade impact wrench? We're planning on NMC-111 chemistry. It should deliver sustained high current draw for burst torque, and needs to be robust enough to survive drops from a 2-meter height. This is a prototype, so cost is secondary to getting the specs right.

---

## P-455

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C1, C4 |

**Prompt:**

> Generate parameters for a prismatic LFP cell, 5.5 Ah, targeting power tools.

**Contradiction:** Operating at -40 deg C with 3.1C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-456

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 cylindrical cell:
> - Capacity: approximately 11.3 Ah
> - Nominal voltage: 3.7 V
> - Application: consumer electronics battery
> - Temperature range: 0 deg C to 40 deg C

---

## P-457

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> NMC-111 cylindrical, 100 Ah for grid storage. Full design please. [Design variant 46]

---

## P-458

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C4 |

**Prompt:**

> Our application is a high-performance electric sports car that operates in Arctic conditions — we need reliable performance down to -40 deg C. It also needs to accept fast charging at 4.0C when plugged in at a remote charging station. Is that feasible? Budget is not the primary concern here — performance is.

**Contradiction:** Operating at -40 deg C with 4.0C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-459

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | CY1, CY5 |

**Prompt:**

> Is it possible to design an 18650-format cell with 59.3 Ah capacity for a mid-size EV platform for a European OEM? We want to leverage the existing supply chain for that format. We're on a tight timeline for this.

**Contradiction:** Requesting 59.3 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-460

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell with the following requirements:
> - Capacity: 129.8 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 255 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles

---

## P-461

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 prismatic cell with the following requirements:
> - Capacity: 12.4 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 184 Wh/kg
> - Application: consumer electronics battery
> - Operating temperature: 0 deg C to 40 deg C
> - Target cycle life: 500 cycles

---

## P-462

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> Design a 11.1 Ah NMC-111 prismatic cell for consumer electronics.

**Contradiction:** Using a 4.3 micron separator with 4.3C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-463

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C4, C1 |

**Prompt:**

> Need a pouch cell: NMC-622, around 4.3 Ah, for power tools application.

**Contradiction:** Using a 3.8 micron separator with 5.0C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-464

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Need a prismatic cell: NMC-111, around 50 Ah, for consumer electronics application.

---

## P-465

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | CY1, CY5 |

**Prompt:**

> We want to use standard 18650 cells for a mid-size EV platform for a European OEM to keep costs down, but we need at least 80.0 Ah per cell. Our pack design is optimized for that form factor. Can it be done? Reliability over the full warranty period is essential.

**Contradiction:** Requesting 80.0 Ah from an 18650 cylindrical format is volumetrically impossible. Even with the highest energy density cathodes, an 18650 can hold at most ~5 Ah.

---

## P-466

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Can you design a cell for a contractor's reciprocating saw used on job sites? Please use LFP chemistry. It should not overheat during continuous heavy-load operation, and needs to keep total pack weight under 800 grams. The client is flexible on dimensions but firm on weight.

---

## P-467

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C2 |

**Prompt:**

> We're designing a laptop that needs to last 12 hours that needs maximum range but also needs to handle very fast charging — at least 5.7C continuous. Energy density should be above 282 Wh/kg. Weight is absolutely critical. Our manufacturing partner has experience with this form factor.

**Contradiction:** Requesting 282.6 Wh/kg energy density with 5.7C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-468

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a LFP pouch battery: 50 Ah, consumer electronics use.

---

## P-469

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete prismatic cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 286.2 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 209 Wh/kg
>   Temperature range: -20 deg C to 55 deg C
>   Cycle life requirement: 7578 cycles minimum

---

## P-470

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | ev_traction |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C1, C4 |

**Prompt:**

> Please generate a complete pouch cell design for electric vehicle traction battery.
> 
> Key specifications:
>   Chemistry: NMC-622 (LiNi0.6Mn0.2Co0.2O2)
>   Cell capacity: 98 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 229 Wh/kg
>   Temperature range: -40 deg C to 45 deg C
>   Cycle life requirement: 1500 cycles minimum
> - Continuous discharge rate: 4.9C

**Contradiction:** Operating at -40 deg C with 4.9C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-471

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Specify a NMC-811 cylindrical battery: 50 Ah, grid storage use.

---

## P-472

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-811 pouch cell with the following requirements:
> - Capacity: 2.6 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 296 Wh/kg
> - Application: cordless power tool battery
> - Operating temperature: -19 deg C to 54 deg C
> - Target cycle life: 1504 cycles

---

## P-473

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C2 |

**Prompt:**

> We're designing a next-generation foldable phone that needs maximum range but also needs to handle very fast charging — at least 4.0C continuous. Energy density should be above 292 Wh/kg. Weight is absolutely critical. We need to hit a specific price point, so don't over-engineer it.

**Contradiction:** Requesting 292.1 Wh/kg energy density with 4.0C continuous discharge creates an impossible thermal management scenario. High energy density requires thick electrodes which cannot sustain high C-rates without severe degradation.

---

## P-474

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | power_tools |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Looking for a battery cell for a cordless circular saw. Safety and thermal stability are paramount. Priority is a cell that can handle the vibration and shock of professional job site use. As for size, it should use a compact form factor that doesn't unbalance the tool. Safety certification is a top priority.

---

## P-475

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a LFP pouch battery cell.
> 
> Requirements:
> * Target capacity: 259 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 146 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -10 deg C and 50 deg C
> * Cycle life goal: 5000+

---

## P-476

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C4, C1 |

**Prompt:**

> We're deploying a next-generation foldable phone in northern Canada where temperatures regularly drop to 0 deg C. The vehicles still need to fast-charge at 4.5C at those temperatures. What cell design would work here? We've already locked in the module architecture, so the cell needs to fit.

**Contradiction:** Using a 3.6 micron separator with 4.5C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-477

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C2 |

**Prompt:**

> We're designing a residential solar energy storage system that needs maximum range but also needs to handle very fast charging — at least 0.9C continuous. Energy density should be above 311 Wh/kg. Weight is absolutely critical. This is a prototype, so cost is secondary to getting the specs right.

**Contradiction:** Targeting 311.8 Wh/kg energy density with 10864 cycle life is a fundamental tradeoff conflict. High energy density NMC-811 cathodes degrade faster due to structural instability at high states of charge.

---

## P-478

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> Design a 50 Ah NMC-111 cylindrical cell for EV traction.

---

## P-479

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> Need a cell design for a backup power system for a data center. We've decided on NMC-111 for the cathode. The deployment requires cells that last at least 10 years of daily cycling, and we need to prioritize cost per kWh over weight or volume.

---

## P-480

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a NMC-111 pouch battery cell.
> 
> Requirements:
> * Target capacity: 9.7 Ah
> * Nominal voltage: 3.7 V
> * Energy density: at least 217 Wh/kg
> * End use: cordless power tool battery
> * Must operate between -20 deg C and 54 deg C
> * Cycle life goal: 1443+

---

## P-481

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | underspecified |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 cylindrical cell:
> - Nominal voltage: 3.7 V
> - Application: stationary grid energy storage
> - Cycle life: 5000 cycles

---

## P-482

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-811 |
| Application | consumer_electronics |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a wireless earbud charging case. Range is everything here — maximize energy per kilogram. Performance-wise, it should deliver stable voltage throughout the discharge curve. Size-wise, it needs to weigh under 50 grams for a phone-class cell.

---

## P-483

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | ev_traction |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're building a commercial electric delivery van and need a battery cell design. We want something that will last thousands of cycles. The cell should deliver consistent power in both highway cruise and stop-and-go driving.use a form factor compatible with CTP (cell-to-pack) architecture This is a prototype, so cost is secondary to getting the specs right.

---

## P-484

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | natural_language |

**Prompt:**

> We need a battery solution for a tablet for professional use. We're planning on NMC-111 chemistry. Performance-wise, it should retain at least 80% health after 500 charge cycles. Size-wise, it needs to be as thin as possible for a slim laptop design. The R&D team wants to push boundaries on this one.

---

## P-485

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Please generate a complete cylindrical cell design for stationary grid energy storage.
> 
> Key specifications:
>   Chemistry: NMC-811 (LiNi0.8Mn0.1Co0.1O2)
>   Cell capacity: 287.2 Ah
>   Voltage: 3.65 V nominal
>   Energy density target: 290 Wh/kg
>   Temperature range: -11 deg C to 54 deg C
>   Cycle life requirement: 6680 cycles minimum

---

## P-486

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | terse |

**Prompt:**

> NMC-811 cylindrical, 5.2 Ah for power tools. Full design please.

---

## P-487

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a LFP prismatic battery cell.
> 
> Requirements:
> * Target capacity: 286.9 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 176 Wh/kg
> * End use: stationary grid energy storage
> * Must operate between -17 deg C and 55 deg C
> * Cycle life goal: 7651+

---

## P-488

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | C2, C6 |

**Prompt:**

> Specify a LFP prismatic battery: 197.8 Ah, grid storage use.

**Contradiction:** LFP chemistry physically cannot achieve 265.2 Wh/kg at cell level (practical max ~180 Wh/kg). The energy density target is incompatible with the LFP cathode material limits.

---

## P-489

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-811 |
| Application | ev_traction |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I'm looking for a battery design for an electric SUV with 500 km range target. Gravimetric energy density is our top priority. Key priorities: the cell must maintain at least 80% capacity after 1500 full cycles, and fit within a standard skateboard platform. We need to hit a specific price point, so don't over-engineer it.

---

## P-490

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | LFP |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | terse |

**Prompt:**

> Specify a LFP pouch battery: 118.6 Ah, grid storage use.

---

## P-491

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C4 |

**Prompt:**

> Our application is a commercial peak-shaving installation that operates in Arctic conditions — we need reliable performance down to -40 deg C. It also needs to accept fast charging at 3.5C when plugged in at a remote charging station. Is that feasible? We may iterate on this, so give us a good starting point.

**Contradiction:** Operating at -40 deg C with 3.5C charging rate is physically dangerous. At extreme cold, lithium ion diffusion slows dramatically, causing lithium plating on the anode even at moderate charge rates.

---

## P-492

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | terse |
| Expected Violations | PO5, PO7 |

**Prompt:**

> NMC-111 pouch, 107.8 Ah for power tools. Full design please.

**Contradiction:** A 107.8 Ah pouch cell with packaging offsets under 1 mm is not manufacturable. The seal width is insufficient for reliable hermeticity at this cell size.

---

## P-493

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a backup power system for a data center and need cells that can operate reliably in an unconditioned outdoor enclosure. Please use NMC-111. For the installation, we want to minimize cooling requirements for passive thermal management. Safety certification is a top priority.

---

## P-494

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | LFP |
| Application | consumer_electronics |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> I need a full parametric design for a LFP cylindrical battery cell.
> 
> Requirements:
> * Target capacity: 3.3 Ah
> * Nominal voltage: 3.2 V
> * Energy density: at least 177 Wh/kg
> * End use: consumer electronics battery
> * Must operate between -3 deg C and 44 deg C
> * Cycle life goal: 682+

---

## P-495

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-622 |
| Application | consumer_electronics |
| Difficulty | contradictory |
| Prompt Style | natural_language |
| Expected Violations | C1, C6 |

**Prompt:**

> We need a cell for a portable gaming device with a nominal voltage around 2.34 V to match our legacy power electronics, but we still want best-in-class energy density — above 267 Wh/kg. Can you design something? We're on a tight timeline for this.

**Contradiction:** Requesting 2.34 V nominal voltage with 267.5 Wh/kg is chemically impossible. NMC cathodes inherently operate at 3.6-3.7 V. A lower voltage would require a different cathode that cannot achieve the specified energy density.

---

## P-496

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-811 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | natural_language |

**Prompt:**

> We're designing a microgrid for an off-grid community and need cells that can handle 5000+ deep discharge cycles without significant degradation. Gravimetric energy density is our top priority. For the installation, we want to be designed for easy field replacement of individual cells. This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.

---

## P-497

| Field | Value |
|-------|-------|
| Cell Type | prismatic |
| Chemistry | NMC-622 |
| Application | grid_storage |
| Difficulty | edge_case |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-622 prismatic cell with the following requirements:
> - Capacity: 277.8 Ah
> - Nominal voltage: 3.65 V
> - Target energy density: 253 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -17 deg C to 54 deg C
> - Target cycle life: 7357 cycles

---

## P-498

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-111 |
| Application | power_tools |
| Difficulty | contradictory |
| Prompt Style | detailed |
| Expected Violations | C4, C1 |

**Prompt:**

> Please generate a complete cylindrical cell design for cordless power tool battery.
> 
> Key specifications:
>   Chemistry: NMC-111 (LiNi0.33Mn0.33Co0.33O2)
>   Cell capacity: 10 Ah
>   Voltage: 3.7 V nominal
>   Energy density target: 181 Wh/kg
>   Temperature range: -10 deg C to 50 deg C
>   Cycle life requirement: 1000 cycles minimum
> - Continuous discharge rate: 4.7C
> - Maximum separator thickness: 3.8 microns

**Contradiction:** Using a 3.8 micron separator with 4.7C discharge rate is a serious safety risk. The extreme C-rate generates heat that can cause thermal runaway with such thin separators, and dendrite penetration risk is greatly elevated.

---

## P-499

| Field | Value |
|-------|-------|
| Cell Type | pouch |
| Chemistry | NMC-111 |
| Application | grid_storage |
| Difficulty | standard |
| Prompt Style | detailed |

**Prompt:**

> Design a NMC-111 pouch cell with the following requirements:
> - Capacity: 100 Ah
> - Nominal voltage: 3.7 V
> - Target energy density: 169 Wh/kg
> - Application: stationary grid energy storage
> - Operating temperature: -10 deg C to 50 deg C
> - Target cycle life: 5000 cycles

---

## P-500

| Field | Value |
|-------|-------|
| Cell Type | cylindrical |
| Chemistry | NMC-622 |
| Application | power_tools |
| Difficulty | underspecified |
| Prompt Style | natural_language |

**Prompt:**

> I need a cell design for a landscaping leaf blower. A mid-range energy density chemistry would work well. The cell must deliver sustained high current draw for burst torque. It also has to fit the standard battery bay of our existing tool platform. Our manufacturing partner has experience with this form factor.

---
