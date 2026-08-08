#!/usr/bin/env python3

import random
import math

# ============================================================
# SETTINGS
# ============================================================

OUTPUT_FILE = "models/decorations/model.sdf"

# Number of seaweed clusters
SEAWEED_CLUSTERS = 250

# Blades per cluster
BLADES_PER_CLUSTER = 4

# Number of rocks
ROCK_COUNT = 100

# Environment size
WORLD_SIZE = 90.0

# Keep decorations away from the extreme edges
EDGE_MARGIN = 5.0

# Sand surface approximately around z = 0
SAND_LEVEL = 0.0

# ============================================================
# RANDOM SEED
# ============================================================

random.seed(42)

# ============================================================
# HELPERS
# ============================================================

def random_position():
    x = random.uniform(
        -WORLD_SIZE / 2 + EDGE_MARGIN,
        WORLD_SIZE / 2 - EDGE_MARGIN
    )

    y = random.uniform(
        -WORLD_SIZE / 2 + EDGE_MARGIN,
        WORLD_SIZE / 2 - EDGE_MARGIN
    )

    return x, y


def random_angle():
    return random.uniform(0, 2 * math.pi)


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


# ============================================================
# START MODEL
# ============================================================

lines = []

lines.append('<?xml version="1.0"?>')
lines.append('')
lines.append('<sdf version="1.8">')
lines.append('')
lines.append('  <model name="underwater_decorations">')
lines.append('')
lines.append('    <static>true</static>')
lines.append('')
lines.append('    <link name="decorations_link">')
lines.append('')

# ============================================================
# SEAWEED
# ============================================================

blade_counter = 0

for cluster in range(SEAWEED_CLUSTERS):

    x, y = random_position()

    cluster_rotation = random_angle()

    for blade in range(BLADES_PER_CLUSTER):

        blade_counter += 1

        # ----------------------------------------------------
        # Random blade size
        # ----------------------------------------------------

        height = random.uniform(0.18, 0.55)

        width = random.uniform(0.025, 0.055)

        depth = random.uniform(0.018, 0.035)

        # ----------------------------------------------------
        # Position inside cluster
        # ----------------------------------------------------

        local_x = random.uniform(-0.12, 0.12)
        local_y = random.uniform(-0.12, 0.12)

        # Base is slightly buried in sand
        base_z = random.uniform(-0.12, -0.03)

        blade_z = base_z + height / 2

        # ----------------------------------------------------
        # Natural bending
        # ----------------------------------------------------

        pitch = random.uniform(-0.18, 0.18)

        roll = random.uniform(-0.12, 0.12)

        yaw = cluster_rotation + random.uniform(-0.35, 0.35)

        # ----------------------------------------------------
        # Seaweed colors
        # ----------------------------------------------------

        green_variation = random.uniform(0.0, 0.08)

        ambient_g = 0.20 + green_variation
        diffuse_g = 0.38 + green_variation

        visual_name = f"seaweed_blade_{blade_counter}"

        lines.append(f'      <visual name="{visual_name}">')

        lines.append(
            f'        <pose>'
            f'{x + local_x:.3f} '
            f'{y + local_y:.3f} '
            f'{blade_z:.3f} '
            f'{roll:.3f} '
            f'{pitch:.3f} '
            f'{yaw:.3f}'
            f'</pose>'
        )

        lines.append('')

        lines.append('        <geometry>')

        lines.append('          <box>')

        lines.append(
            f'            <size>'
            f'{width:.3f} '
            f'{depth:.3f} '
            f'{height:.3f}'
            f'</size>'
        )

        lines.append('          </box>')

        lines.append('        </geometry>')

        lines.append('')

        lines.append('        <material>')

        lines.append(
            f'          <ambient>'
            f'0.02 {ambient_g:.2f} 0.06 1'
            f'</ambient>'
        )

        lines.append(
            f'          <diffuse>'
            f'0.03 {diffuse_g:.2f} 0.08 1'
            f'</diffuse>'
        )

        lines.append(
            '          <specular>0.01 0.02 0.01 1</specular>'
        )

        lines.append('        </material>')

        lines.append('')

        lines.append('      </visual>')

        lines.append('')


# ============================================================
# ROCKS
# ============================================================

for rock_id in range(ROCK_COUNT):

    x, y = random_position()

    # --------------------------------------------------------
    # Rock size
    # --------------------------------------------------------

    size_x = random.uniform(0.12, 0.45)

    size_y = random.uniform(0.10, 0.38)

    size_z = random.uniform(0.08, 0.30)

    # --------------------------------------------------------
    # Burial depth
    #
    # Negative Z means the rock is pushed into the sand.
    # This makes many rocks appear half buried.
    # --------------------------------------------------------

    burial = random.uniform(0.35, 0.75)

    rock_z = -(size_z * burial)

    # --------------------------------------------------------
    # Rotation
    # --------------------------------------------------------

    roll = random.uniform(-0.25, 0.25)

    pitch = random.uniform(-0.25, 0.25)

    yaw = random_angle()

    visual_name = f"rock_{rock_id}"

    lines.append(f'      <visual name="{visual_name}">')

    lines.append(
        f'        <pose>'
        f'{x:.3f} '
        f'{y:.3f} '
        f'{rock_z:.3f} '
        f'{roll:.3f} '
        f'{pitch:.3f} '
        f'{yaw:.3f}'
        f'</pose>'
    )

    lines.append('')

    lines.append('        <geometry>')

    lines.append('          <box>')

    lines.append(
        f'            <size>'
        f'{size_x:.3f} '
        f'{size_y:.3f} '
        f'{size_z:.3f}'
        f'</size>'
    )

    lines.append('          </box>')

    lines.append('        </geometry>')

    lines.append('')

    lines.append('        <material>')

    lines.append(
        '          <ambient>0.12 0.11 0.09 1</ambient>'
    )

    lines.append(
        '          <diffuse>0.25 0.23 0.19 1</diffuse>'
    )

    lines.append(
        '          <specular>0.03 0.03 0.03 1</specular>'
    )

    lines.append('        </material>')

    lines.append('')

    lines.append('      </visual>')

    lines.append('')


# ============================================================
# CLOSE MODEL
# ============================================================

lines.append('    </link>')
lines.append('')
lines.append('  </model>')
lines.append('')
lines.append('</sdf>')
lines.append('')

# ============================================================
# WRITE FILE
# ============================================================

with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(lines))

print("==============================================")
print("UNDERWATER DECORATIONS GENERATED")
print("==============================================")
print(f"Seaweed clusters : {SEAWEED_CLUSTERS}")
print(f"Seaweed blades   : {blade_counter}")
print(f"Rocks            : {ROCK_COUNT}")
print(f"Total visuals    : {blade_counter + ROCK_COUNT}")
print("----------------------------------------------")
print(f"Saved to: {OUTPUT_FILE}")
print("==============================================")