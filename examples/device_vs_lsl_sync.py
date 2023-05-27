from itertools import chain
from pathlib import Path

import pandas as pd
import seaborn as sns
from rich import print
from rich.traceback import install

from pupil_labs.lsl_relay.linear_time_model import TimeAlignmentModels

time_domain_key = "Pupil Companion Device"

install()
sns.set(font_scale=1.5)

illuminance_files = sorted(
    Path("./companion_app_exports").glob("subject_*/*.illuminance.csv")
)
print(f"Illuminance files: {sorted(map(str, illuminance_files))}")
companion_device_dfs = {f: pd.read_csv(f) for f in illuminance_files}

for path, df in companion_device_dfs.items():
    df["path"] = path
    df["time"] = pd.to_datetime(df["timestamp [ns]"], unit="ns")
    df["time [s]"] = df["timestamp [ns]"] * 1e-9
    df["subject"] = path.parent.name
    df["eye"] = path.stem.split(" ")[1]

    ill_min = df.illuminance.min()
    ill_max = df.illuminance.max()
    df["illuminance (normalized)"] = (df.illuminance - ill_min) / (ill_max - ill_min)

    df["time domain"] = time_domain_key

lsl_time_dfs = {p: df.copy() for p, df in companion_device_dfs.items()}
for path, df in lsl_time_dfs.items():
    assert (df.path == path).all()
    model_path = path.with_name("time_alignment_parameters.json")
    models = TimeAlignmentModels.read_json(model_path)
    df["time [s]"] = df["timestamp [ns]"] * 1e-9

    df["time [s]"] = models.cloud_to_lsl.predict(df[["time [s]"]].values)
    df["time domain"] = "Lab Streaming Layer"

illuminance_df = pd.concat(
    chain(companion_device_dfs.values(), lsl_time_dfs.values()), ignore_index=True
)


for time_domain in (time_domain_key, "Lab Streaming Layer"):
    for eye in ("left", "right"):
        mask = (illuminance_df["time domain"] == time_domain) & (
            illuminance_df.eye == eye
        )
        illuminance_df.loc[mask, "time [s]"] -= illuminance_df.loc[
            mask, "time [s]"
        ].min()

fg = sns.relplot(
    kind="line",
    data=illuminance_df,
    x="time [s]",
    y="illuminance (normalized)",
    col="eye",
    hue="subject",
    row="time domain",
    aspect=1,
    facet_kws=dict(sharex=False),
)
fg.set_titles(template="{row_var} =\n{row_name}\n—\n{col_var} = {col_name}")
fg.tight_layout()

output_path = Path("illuminance_over_time.png").resolve()
print(f"Saving figure to {output_path}")
fg.savefig(output_path, dpi=120)
