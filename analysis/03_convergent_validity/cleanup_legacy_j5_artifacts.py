from pathlib import Path

import matplotlib.pyplot as plt

BASE = Path('/home/ubuntu/small-groups-comm-metrics')
V1_DIR = BASE / 'figures/03_convergent_validity/temporal_meetings_v1'
V2_DIR = BASE / 'figures/03_convergent_validity/temporal_meetings_v2'
ARCHIVE_DIR = BASE / 'figures/03_convergent_validity/temporal_meetings_archived_exclusions'

LEGACY_NAME = 'J5S2_Team6_ScenarioB_temporal_comparison.png'
PLACEHOLDER_TEXT = (
    'Excluded from corrected Step 03 outputs\n\n'
    'Meeting: J5S2_Team6_ScenarioB\n'
    'Reason: unsupported workbook schema\n'
    'Action: removed from temporal_meetings_v2 analytical set\n\n'
    'The v1 analytical image was archived to avoid confusion with the corrected results.'
)


def archive_legacy_image() -> tuple[Path, Path | None]:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    source = V1_DIR / LEGACY_NAME
    destination = ARCHIVE_DIR / LEGACY_NAME
    if source.exists():
        source.rename(destination)
        return destination, source
    return destination, None


def make_placeholder() -> Path:
    V2_DIR.mkdir(parents=True, exist_ok=True)
    output = V2_DIR / LEGACY_NAME

    fig = plt.figure(figsize=(14, 8), facecolor='white')
    ax = fig.add_subplot(111)
    ax.axis('off')

    fig.suptitle(
        'Temporal metric comparison unavailable: J5S2_Team6_ScenarioB',
        fontsize=22,
        fontweight='bold',
        y=0.96,
    )

    ax.text(
        0.5,
        0.56,
        PLACEHOLDER_TEXT,
        ha='center',
        va='center',
        fontsize=18,
        linespacing=1.6,
        bbox=dict(boxstyle='round,pad=0.8', facecolor='#f8f8f8', edgecolor='#555555', linewidth=1.5),
        transform=ax.transAxes,
    )

    ax.text(
        0.5,
        0.17,
        'This placeholder is intentional and documents the corrected Step 03 exclusion policy.',
        ha='center',
        va='center',
        fontsize=13,
        color='#444444',
        transform=ax.transAxes,
    )

    fig.savefig(output, dpi=180, bbox_inches='tight')
    plt.close(fig)
    return output


if __name__ == '__main__':
    archived_path, moved_from = archive_legacy_image()
    placeholder_path = make_placeholder()
    print(f'archived_path={archived_path}')
    print(f'moved_from={moved_from}')
    print(f'placeholder_path={placeholder_path}')
