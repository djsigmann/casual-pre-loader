#!/bin/bash

set -e

ERR=false

TERM_OPTS="$(stty -g)"
trap 'stty "${TERM_OPTS}"' 0 1 2 3 15

# two dirs up
cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")"

log() (
	level="${1}"
	fmt="${2:-"%s\\t%s\\n"}"
	fmt="%s ${fmt}"

	while read -r line; do
		printf "${fmt}" "$(date '+[%Y-%m-%d %H:%M:%S %Z%z]')" "${level}" "${line}"
	done >&2
)

log_color() { log "${1}" "\\033[${2}m%s\\033[0m\\t\033[${2}m%s\\033[0m\\n"; }

debug() { log_color DEBUG 32; }
info() { log_color INFO 34; }
err() { log_color ERROR 31; }
warn() { log_color WARNING 33; }

_dep_missing_install() {
	printf \
		'Debian/Ubuntu:
	  apt install %s
	Arch:
	  pacman -S %s
	Fedora:
	  dnf install %s
	' "${@}"
}

dep_missing() {
	printf '%s is not installed, please install it using your package manager\n' "${1}"
}

prompt() {
	[ -t 0 ] || return 1

	stty raw -echo

	printf '%s' "${1}" >&2
	printf '%s' "$(head -c 1)"

	stty "${TERM_OPTS}"

	printf '\n' >&2
}

prompt_yn() {
	! [ -t 0 ] && printf n && return

	set -- "${1}" "${2:-y}"
	[ "${2}" = y ] &&
		set -- "${1} [Y/n]" "${2}" ||
		set -- "${1} [y/N]" "${2}"

	case "$(prompt "${1}")" in
	[yY]) printf 'y' ;;
	[nN]) printf 'n' ;;
	*) printf '%s' "${2}" ;;
	esac
}

! command -v python3 >/dev/null 2>&1 && ERR=true &&
	dep_missing python3 | err

! python3 -m pip --version >/dev/null 2>&1 && ERR=true &&
	dep_missing pip | err

! python3 -m venv --help >/dev/null 2>&1 && ERR=true &&
	dep_missing 'python venv module' | err

# check for wine
! command -v wine >/dev/null 2>&1 &&
	dep_missing wine | warn &&
	printf '%s\n' 'Wine is required to run studiomdl.exe for model precaching' | warn &&
	{ ${ERR} || [ "$(prompt_yn 'Continue anyway?' n)" != y ]; } && ERR=true

${ERR} && exit 1 # exit if errors were previously raised

if [ -f 'requirements.txt' ]; then
	! [ -d '.venv' ] &&
		printf '%s\n' 'Creating virtual environment' | info &&
		python3 -m venv .venv | info

	. .venv/bin/activate

	pip install --upgrade pip | info

	printf '%s\n' 'Installing dependencies' | info
	pip install --upgrade -r requirements.txt | info
fi

printf '%s\n' 'Starting Casual Preloader' | info
exec ./main.py
