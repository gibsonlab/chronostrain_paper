from pathlib import Path
import click
import math


class NoInferenceRunError(BaseException):
    pass


def extract_last_epoch(log_path: Path) -> float:
    last_epoch = None
    with open(log_path, "rt") as f:
        for line in f:
            if "Average ELBO =" not in line:
                continue

            tokens = line.split("|")
            iter_token = tokens[0].strip()
            last_epoch = int(iter_token.split()[-1])
    if last_epoch is None:
        raise NoInferenceRunError()
    else:
        return last_epoch


@click.command()
@click.option(
    '--participant', '-p', 'target_participant',
    type=str,
    required=True,
    help="The participant ID."
)
def main(
        target_participant: str
):
    target_logfile = Path("/mnt/e/infant_nt") / target_participant / 'chronostrain' / 'inference.log'

    if target_logfile.exists():
        try:
            last_epoch = extract_last_epoch(target_logfile)
            print("{}: Last Epoch: {}".format(target_participant, last_epoch))
        except NoInferenceRunError as e:
            print("{}: No ELBO value parsed from logfile.".format(target_participant))
    else:
        print("{}: Logfile not found.".format(target_participant))


if __name__ == "__main__":
    main()
