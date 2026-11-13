from dataclasses import dataclass
from drafter import *
from bakery import assert_equal

# classes

@dataclass
class VehicleSetup:
    tire_diameter: float
    redline: float
    final_drive: float
    gear_ratios: list[float]

@dataclass
class GearResult:
    gear_number: int
    gear_ratio: float
    overall_ratio: float
    speed_mph: float
    engine_rpm: float
    warning: str

@dataclass
class State:
    setups: list[VehicleSetup]
    active_setup_index: int
    target_speed: float
    results: list[GearResult]
    message: str

#calculation

def calculate_speed(rpm: float, tire_diameter: float, gear_ratio: float, final_drive: float) -> float:
    speed = rpm * tire_diameter / (gear_ratio * final_drive * 336.135)
    return speed

def calculate_rpm(speed: float, tire_diameter: float, gear_ratio: float, final_drive: float) -> float:
    rpm = speed * 336.135 * gear_ratio * final_drive / tire_diameter
    return rpm

def parse_gear_ratios(gear_text: str) -> list[float]:
    parts = gear_text.split(",")
    ratios = []
    for p in parts:
        ratios.append(float(p.strip()))
    return ratios

def valid_setup(setup: VehicleSetup) -> bool:
    if setup.tire_diameter <= 0:
        return False
    if setup.redline <= 0:
        return False
    if setup.final_drive <= 0:
        return False
    if len(setup.gear_ratios) == 0:
        return False
    for ratio in setup.gear_ratios:
        if ratio <= 0:
            return False
    return True

def calculate_speed_results(setup: VehicleSetup) -> list[GearResult]:
    results = []
    gear = 1
    for ratio in setup.gear_ratios:
        overall = ratio * setup.final_drive
        speed = calculate_speed(setup.redline, setup.tire_diameter, ratio, setup.final_drive)
        results.append(GearResult(gear, ratio, overall, speed, setup.redline, ""))
        gear = gear + 1
    return results

def calculate_rpm_results(setup: VehicleSetup, target_speed: float) -> list[GearResult]:
    results = []
    gear = 1
    for ratio in setup.gear_ratios:
        overall = ratio * setup.final_drive
        rpm = calculate_rpm(target_speed, setup.tire_diameter, ratio, setup.final_drive)
        warning = "Within redline"
        if rpm > setup.redline:
            warning = "Above redline"
        results.append(GearResult(gear, ratio, overall, target_speed, rpm, warning))
        gear += 1
    return results

#home page

@route
def index(state: State) -> Page:
    return Page(state, ["RACEGEAR",
                        "Automotive Gear Ratio Calculator",
                        "",
                        "Welcome to RaceGear!",
                        "This website lets you calculate gear speeds and engine RPM.",
                        "You can also compare different gearing setups.",
                        "",
                        "Things you can do:",
                        "- Calculate speed in each gear",
                        "- Find engine RPM at a certain speed",
                        "- Compare two setups",
                        "",
                        Button("Enter Vehicle Setup", "vehicle_setup_page"),
                        Button("View Saved Setups", "gear_results_page")])

# vehicle setup

@route
def vehicle_setup_page(state: State) -> Page:
    return Page(state, ["VEHICLE SETUP",
                        "Enter the vehicle information.", "",
                        "Tire Diameter:",
                        TextBox("tire_diameter", 25.0), "",
                        "Engine Redline:",
                        TextBox("redline", 7000.0),
                        "",
                        "Final Drive:",
                        TextBox("final_drive", 3.73),
                        "",
                        "Gear Ratios (separate with commas):",
                        TextBox("gear_ratios", "3.20, 2.10, 1.50, 1.20, 1.00, 0.80"),
                        "",
                        Button("Calculate Gear Speeds", "calculate_speeds"),
                        Button("Home", "index")])

# calculate speeds

@route
def calculate_speeds(state: State, tire_diameter: float,
                     redline: float, final_drive: float, gear_ratios: str) -> Page:
    ratios = parse_gear_ratios(gear_ratios)
    setup = VehicleSetup(tire_diameter, redline, final_drive, ratios)

    if valid_setup(setup):
        state.setups.append(setup)
        state.active_setup_index = len(state.setups) - 1
        state.results = calculate_speed_results(setup)
        state.message = "Calculations finished!"
        return gear_results_page(state)
    else:
        state.message = "Invalid values. Make sure everything is positive."
        return Page(state, ["INVALID SETUP",
                            state.message,
                            Button("Try Again", "vehicle_setup_page"),
                            Button("Home", "index")])
# results page

@route
def gear_results_page(state: State) -> Page:
    if len(state.setups) == 0:
        return Page(state, ["No setups saved yet.",
                            Button("Enter Vehicle Setup", "vehicle_setup_page"),
                            Button("Home", "index")])

    setup = state.setups[state.active_setup_index]
    content = ["GEAR RESULTS",
               state.message,
               "",
               "Tire Diameter: " + str(setup.tire_diameter),
               "Redline: " + str(setup.redline),
               "Final Drive: " + str(setup.final_drive),
               "",
               "SPEED AT REDLINE",
               ""]
    for result in state.results:
        content.append("Gear " + str(result.gear_number))
        content.append("Speed: " + str(round(result.speed_mph, 2)) + " MPH")
        content.append("Gear Ratio: " + str(result.gear_ratio))
        content.append("Overall Ratio: " + str(round(result.overall_ratio, 3)))
        content.append("")

    content.extend(["These are theoretical speeds, actual speeds may be different.",
                    "",
                    Button("Calculate RPM", "rpm_page"),
                    Button("Compare Setups", "comparison_page"),
                    Button("Enter Another Vehicle", "vehicle_setup_page"),
                    Button("Home", "index")])
    return Page(state, content)

#rpm calculator

@route
def rpm_page(state: State) -> Page:
    if len(state.setups) == 0:
        return Page(state, ["Enter a setup first.",
                            Button("Enter Setup", "vehicle_setup_page")])
    return Page(state, ["RPM CALCULATOR",
                        "Enter a speed below.",
                        "",
                        "Target Speed MPH:",
                        TextBox("target_speed", 60.0),
                        "",
                Button("Calculate RPM", "calculate_target_rpm"),
                Button("Back", "gear_results_page"),
                Button("Home", "index")])


# calculate rpm

@route
def calculate_target_rpm(state: State, target_speed: float) -> Page:
    if len(state.setups) == 0:
        return Page(state, ["Enter a setup first.",
                            Button("Enter Setup", "vehicle_setup_page")])

    if target_speed <= 0:
        state.message = "Speed needs to be above zero."
        return Page(state, [
            state.message,
            Button("Try Again", "rpm_page")])
    setup = state.setups[state.active_setup_index]
    state.target_speed = target_speed
    state.results = calculate_rpm_results(setup, target_speed)
    state.message = "RPM calculated at " + str(target_speed) + " MPH"

    content = ["RPM RESULTS",
                state.message,
                "",
                "Target Speed: " + str(target_speed),
                ""]
    for result in state.results:
        content.append("Gear " + str(result.gear_number))
        content.append(str(round(result.engine_rpm, 2)) + " RPM")
        content.append(result.warning)
        content.append("")

    content.extend([Button("Try Another Speed", "rpm_page"),
                    Button("Back to Results", "gear_results_page"),
                    Button("Home", "index")])
    return Page(state, content)

# compare page

@route
def comparison_page(state: State) -> Page:
    if len(state.setups) == 0:
        return Page(state, ["Enter a setup first.",
                            Button("Enter Setup", "vehicle_setup_page")])
    setup = state.setups[state.active_setup_index]
    return Page(state, ["COMPARE SETUPS",
                        "Enter another final drive and gear ratios.",
                        "Tire diameter and redline will stay the same.",
                        "",
                        "Current Final Drive: " + str(setup.final_drive),
                        "",
                        "New Final Drive:",
                        TextBox("second_final_drive", 4.10),
                        "",
                        "New Gear Ratios:",
                        TextBox("second_gear_ratios", "3.50, 2.20, 1.60, 1.20, 1.00, 0.85"),
                        "",
                        Button("Compare", "compare_setups"),
                        Button("Back", "gear_results_page"),
                        Button("Home", "index")])

# compare calculations

@route
def compare_setups(state: State, second_final_drive: float, second_gear_ratios: str) -> Page:

    if len(state.setups) == 0:
        return Page(state, ["Enter a setup first.",
                            Button("Enter Setup", "vehicle_setup_page")])

    original = state.setups[state.active_setup_index]
    ratios = parse_gear_ratios(second_gear_ratios)

    second = VehicleSetup(original.tire_diameter,
                          original.redline, second_final_drive, ratios)

    if not valid_setup(second):
        state.message = "Invalid second setup."
        return Page(state, [state.message,
                            Button("Try Again", "comparison_page")])
    elif len(original.gear_ratios) != len(ratios):
        state.message = "Both setups need the same number of gears."
        return Page(state, [state.message,
                            Button("Try Again", "comparison_page")])
    else:
        original_results = calculate_speed_results(original)
        second_results = calculate_speed_results(second)

        state.setups.append(second)
        state.active_setup_index = len(state.setups) - 1
        state.results = second_results
        state.message = "Comparison finished!"
        content = ["GEAR COMPARISON",
                   "", "Original Final Drive: " + str(original.final_drive),
                   "New Final Drive: " + str(second.final_drive),
                   "",
                   "SPEED AT REDLINE", ""]

        for i in range(len(original_results)):
            speed1 = original_results[i].speed_mph
            speed2 = second_results[i].speed_mph
            difference = speed2 - speed1
            content.append("Gear " + str(i + 1))
            content.append("Original: " + str(round(speed1, 2)) + " MPH")
            content.append("New: " + str(round(speed2, 2)) + " MPH")
            content.append("Difference: " + str(round(difference, 2)) + " MPH")
            if difference > 0:
                content.append("New setup is faster.")
            elif difference < 0:
                content.append("Original setup is faster.")
            else:
                content.append("Both are the same.")
            content.append("")

        content.extend([Button("Compare Again", "comparison_page"),
                        Button("View New Results", "gear_results_page"),
                        Button("Home", "index")])
        return Page(state, content)

# tests


test_setup = VehicleSetup(25.0, 7000.0, 3.73, [3.20, 2.10, 1.50, 1.20, 1.00, 0.80])
assert_equal(round(calculate_speed(7000, 25, 0.80, 3.73), 2), 174.47)
assert_equal(round(calculate_rpm(174.47, 25, 0.80, 3.73)), 7000)
assert_equal(parse_gear_ratios("3.20, 2.10, 1.50"), [3.20, 2.10, 1.50])
assert_equal(valid_setup(test_setup), True)

bad_setup = VehicleSetup(0, 7000, 3.73, [3.20, 2.10])
assert_equal(valid_setup(bad_setup), False)
assert_equal(len(calculate_speed_results(test_setup)), 6)
assert_equal(round(calculate_speed_results(test_setup)[0].speed_mph, 2), 43.62)


# website info

set_site_information("Reilly Ritenour",
                     "RaceGear is a gearing calculator for vehicle speed and RPM.",
                     "Made with Python and Drafter. Uses the 336.135 conversion factor.",
                     "See the RaceGear planning document in the GitHub repository.", [])
hide_debug_information()
set_website_framed(False)
start_server(State([], 0, 0.0, [], "Welcome to RaceGear!"), site_title="RaceGear")

