#!/bin/sh

set -e

MIN_PYTHON_VERSION=3.12

# shellcheck disable=SC2312
cd "$(dirname "$(dirname "$(realpath -s "${0}")")")" # one dir up

_log() (
	set -e

	level="${1}"
	fmt="%s ${2:-'%s %s\n'}"
	date="$(date '+[%Y-%m-%d %H:%M:%S]')"

	while read -r line; do
		# shellcheck disable=SC2059
		printf "${fmt}" "${date}" "${level}" "${line}"
	done >&2
)

_log_color() { _log "${1}" "\\033[${2}m%-${max_len_level}s\\033[0m\033[${2}m%s\\033[0m\\n"; }

max_len_level=0
for _level in debug:32 info:34 warning:33 error:31; do
	level="${_level%:*}"

	# shellcheck disable=SC2312
	max_len_level="$(printf '%s\n' "${max_len_level}" "${#level}" | sort -n | tail -n1)"

	# shellcheck disable=SC2312
	eval "${level}() { _log_color $(printf '%s' "${level}" | tr '[:lower:]' '[:upper:]') ${_level##*:}; }"
done
unset level _level
: $((max_len_level += 2)) # apply 2 spaces of padding

dep_missing() { printf '%s is not installed, please install it according to your distro\n' "${1}"; }

intcmp() {
	printf '%s' "$((($1 > $2) - ($1 < $2)))"
}

check_min_python_version() (
	set -e

	version="$(python -V)" version="${version#Python }"

	major="${1%%.*}"
	_major="${version%%.*}"

	ret=true
	# shellcheck disable=SC2249
	case "$(intcmp "${_major:-0}" "${major:-0}")" in
	0)
		rest="${1#"${major}"}" rest="${rest#.}"
		minor="${rest%%.*}"
		_rest="${version#"${_major}"}" _rest="${_rest#.}"
		_minor="${_rest%%.*}"
		case "$(intcmp "${_minor:-0}" "${minor:-0}")" in
		0)
			patch="${rest#"${minor}"}" patch="${patch#.}"
			_patch="${_rest#"${_minor}"}" _patch="${_patch#.}"
			case "$(intcmp "${_patch:-0}" "${patch:-0}")" in
			-1) ret=false ;;
			esac
			;;
		-1) ret=false ;;
		esac
		;;
	-1) ret=false ;;
	esac

	printf '%s' "${version}"

	${ret}
)

mkvenv() { python3 -m venv --system-site-packages .venv; }

# shellcheck disable=SC2312
[ "$(id -u)" -eq 0 ] && {
	printf "This script should not be run as root\n" | error
	exit 1
}

ERROR=false

(
	set -e

	# shellcheck disable=SC2310
	command -v python3 >/dev/null 2>&1 || {
		dep_missing python3 | error
		false # none of the other commands in this subshell will work without python
	}

	# shellcheck disable=SC2310
	pyver="$(check_min_python_version "${MIN_PYTHON_VERSION}")" || {
		ERROR=true
		printf 'Your version of python (%s) is out of date, the minimum required version is Python %s\n' "${pyver}" "${MIN_PYTHON_VERSION}" | error
	}

	# shellcheck disable=SC2310
	python3 -m ensurepip --version >/dev/null 2>&1 || {
		ERROR=true
		dep_missing ensurepip | error
	}

	# shellcheck disable=SC2310
	python3 -c 'import venv' 2>/dev/null || {
		ERROR=true
		dep_missing 'python3-venv' | error
	}

	! ${ERROR}
) || ERROR=true

# check for wine
command -v wine >/dev/null 2>&1 ||
	printf '%s\n' 'Wine is required to run studiomdl.exe for model precaching' | warning

! ${ERROR} || exit 1 # exit if errors were previously raised

if [ -f 'requirements.txt' ]; then
	[ -f '.venv/bin/activate' ] || {
		printf '%s\n' 'Creating virtual environment' | info
		mkvenv
	}

	. .venv/bin/activate

	# shellcheck disable=SC2310
	if ! pyver="$(check_min_python_version "${MIN_PYTHON_VERSION}")"; then
		printf "The virtual environment's version of python (%s) is out of date, the minimum required version is Python %s\n" "${pyver}" "${MIN_PYTHON_VERSION}" | warning

		# shellcheck disable=SC2218
		deactivate # defined by venv

		rm -r .venv
		mkvenv
		. .venv/bin/activate

		check_min_python_version "${MIN_PYTHON_VERSION}" || {
			printf '%s\n' 'unable to recreate the virtual environment with an up-to-date version of python' | error
			exit 1
		}

		printf '%s\n' 'managed to recreate the virtual environment with an up-to-date version of python' | warning
	fi

	printf '%s\n' 'Installing and/or updating dependencies' | info
	{
		export PIP_RETRIES="${PIP_RETRIES:-2}" PIP_TIMEOUT="${PIP_TIMEOUT:-5}"
		python3 -m ensurepip &&
			python3 -m pip install --upgrade pip &&
			python3 -m pip install --upgrade -r requirements.txt
	} || {
		printf 'No internet connection, cannot install and/or update required dependencies\n' | error
		ERROR=true
	}
fi

# ensure that submodules ARE in fact, properly cloned
git submodule update --init --recursive --remote || {
	# shellcheck disable=SC2016
	git submodule update --init --recursive &&
		git submodule foreach --recursive '[ "${sha1}" = "$(git rev-parse HEAD)" ]' &&
		printf 'No internet connection, but submodules seem to be up-to-date, it is advised to retry once an internet connection has been re-established\n' | warning
} || {
	ERROR=true
	printf 'No internet connection, cannot update submodules\n' | error
}

! ${ERROR} || exit 1

printf '%s\n' 'Starting Casual Preloader' | info
exec ./main.py "${@}"
