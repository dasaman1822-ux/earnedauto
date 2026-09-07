# BGL Dataset Analysis

## Dataset

Dataset: BGL (Blue Gene/L supercomputer log)

Source: LogHub

The BGL dataset is a labelled system log dataset from the Blue Gene/L
supercomputer. LogHub reports 4,747,963 log lines covering 214.7 days.

Source:
https://github.com/logpai/loghub

## Local Dataset Statistics

The downloaded BGL.log file was analyzed using `src/analyze_bgl.py`.

Results:

- Total records: 4,747,963
- Normal records: 4,399,503
- Alert records: 348,460
- Alert percentage: 7.34%
- Distinct labels: 42

In the BGL dataset, `-` is used as the normal/non-alert label.
The remaining labels represent alert categories.

## Top Alert Labels

| Alert label | Records |
|---|---:|
| KERNDTLB | 152,734 |
| KERNSTOR | 63,491 | 
| APPSEV | 49,651 |
| KERNMNTF | 31,531 |
| KERNTERM | 23,338 |
| KERNREC | 6,145 |
| APPREAD | 5,983 |
| KERNRTSP | 3,983 |
| APPRES | 2,370 |
| APPUNAV | 2,048 |
| APPTO | 1,991 |
| KERNMICRO | 1,503 |
| APPOUT | 816 |
| KERNMNT | 720 |
| APPBUSY | 512 |

## Initial Interpretation

The alert labels show several broad categories of infrastructure
problems, including kernel, storage/filesystem, application, and
communication-related failures.

The simulator will not reproduce all 42 BGL labels. Instead, the real
BGL distribution will be used to inform a smaller set of incident types
and candidate remediation actions required by the Earned Autonomy
project.

This abstraction is a project simulation choice and is not a claim that
BGL directly defines these six remediation scenarios.

## Reproducibility

The raw BGL dataset is kept outside the Git repository in:

`C:\Users\KIIT0001\earnedauto-data\`

The analysis can be reproduced with:

```text
python src/analyze_bgl.py