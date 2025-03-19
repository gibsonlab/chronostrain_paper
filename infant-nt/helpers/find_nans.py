from pathlib import Path
import click
import math


class NoInferenceRunError(BaseException):
    pass


def extract_last_elbo(log_path: Path) -> float:
    elbo_value = None
    with open(log_path, "rt") as f:
        for line in f:
            if "Average ELBO =" not in line:
                continue

            tokens = line.split("|")
            elbo_token = tokens[2].strip()
            elbo_token = elbo_token.split("=")[1].strip()
            elbo_value = float(elbo_token)
    if elbo_value is None:
        raise NoInferenceRunError()
    else:
        return elbo_value


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
            last_elbo = extract_last_elbo(target_logfile)
            if math.isnan(last_elbo):
                print("{}: Last ELBO: {}".format(target_participant, last_elbo))
            else:
                pass
        except NoInferenceRunError as e:
            print("{}: No ELBO value parsed from logfile.".format(target_participant))
    else:
        print("{}: Logfile not found.".format(target_participant))


if __name__ == "__main__":
    main()
