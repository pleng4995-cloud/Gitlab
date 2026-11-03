import math


def _equivalent_resistance(node):
    if "resistance_ohm" in node:
        resistance = node["resistance_ohm"]
        if not math.isfinite(resistance) or resistance <= 0:
            raise ValueError("Resistance must be a positive finite number.")
        return resistance

    connection = node.get("type")
    components = node.get("components")
    if connection not in ("series", "parallel") or not components:
        raise ValueError("A circuit group must be series or parallel and contain components.")

    resistances = [_equivalent_resistance(component) for component in components]
    if connection == "series":
        return sum(resistances)
    return 1 / sum(1 / resistance for resistance in resistances)


def _analyze_node(node, voltage_v, current_a, results):
    if "resistance_ohm" in node:
        resistance = node["resistance_ohm"]
        results.append({
            "name": node["name"],
            "resistance_ohm": resistance,
            "voltage_v": voltage_v,
            "current_a": current_a,
            "power_w": voltage_v * current_a,
        })
        return

    if node["type"] == "series":
        for component in node["components"]:
            component_voltage = current_a * _equivalent_resistance(component)
            _analyze_node(component, component_voltage, current_a, results)
    else:
        for component in node["components"]:
            component_current = voltage_v / _equivalent_resistance(component)
            _analyze_node(component, voltage_v, component_current, results)


def analyze_circuit(voltage_v, circuit):
    if not math.isfinite(voltage_v):
        raise ValueError("Voltage must be a finite number.")

    total_resistance = _equivalent_resistance(circuit)
    total_current = voltage_v / total_resistance
    components = []
    _analyze_node(circuit, voltage_v, total_current, components)
    return {
        "total_resistance_ohm": total_resistance,
        "current_a": total_current,
        "power_w": voltage_v * total_current,
        "components": components,
    }


def analyze_dc(voltage_v, resistance_ohm):
    if resistance_ohm <= 0:
        raise ValueError("Resistance must be a positive finite number.")
    result = analyze_circuit(voltage_v, {"name": "R1", "resistance_ohm": resistance_ohm})
    return {"current_a": result["current_a"], "power_w": result["power_w"]}


def _read_number(prompt, positive=False):
    while True:
        try:
            value = float(input(prompt))
            if not math.isfinite(value) or (positive and value <= 0):
                raise ValueError
            return value
        except ValueError:
            qualifier = "a positive " if positive else "a finite "
            print(f"Please enter {qualifier}number.")


def _read_count(prompt):
    while True:
        try:
            count = int(input(prompt))
            if count > 0:
                return count
        except ValueError:
            pass
        print("Please enter a positive whole number.")


def _read_choice(prompt, choices):
    while True:
        choice = input(prompt).strip().lower()
        if choice in choices:
            return choice
        print(f"Please choose one of: {', '.join(choices)}.")


def _read_group(connection, next_resistor):
    components = []
    count = _read_count("Number of components in this group: ")
    for index in range(count):
        print(f"Component {index + 1}:")
        kind = _read_choice("  Resistor or nested group? [r/g]: ", ("r", "g"))
        if kind == "r":
            name = f"R{next_resistor[0]}"
            next_resistor[0] += 1
            resistance = _read_number(f"  Resistance for {name} (ohm): ", positive=True)
            components.append({"name": name, "resistance_ohm": resistance})
        else:
            nested_connection = _read_choice(
                "  Nested connection [s]eries/[p]arallel: ", ("s", "p")
            )
            nested_type = "series" if nested_connection == "s" else "parallel"
            components.append(_read_group(nested_type, next_resistor))
    return {"type": connection, "components": components}


def main():
    voltage = _read_number("Source voltage (V): ")
    connection = _read_choice("Overall connection [s]eries/[p]arallel: ", ("s", "p"))
    circuit_type = "series" if connection == "s" else "parallel"
    circuit = _read_group(circuit_type, [1])
    result = analyze_circuit(voltage, circuit)

    print(f"\nEquivalent resistance: {result['total_resistance_ohm']:.4g} ohm")
    print(f"Total current: {result['current_a']:.4g} A")
    print(f"Total power: {result['power_w']:.4g} W")
    print("\nComponent results:")
    for component in result["components"]:
        print(
            f"{component['name']}: {component['resistance_ohm']:.4g} ohm, "
            f"{component['voltage_v']:.4g} V, {component['current_a']:.4g} A, "
            f"{component['power_w']:.4g} W"
        )


if __name__ == "__main__":
    main()