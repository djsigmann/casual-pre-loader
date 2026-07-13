#!/bin/sh

set -e

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

# shellcheck disable=SC2312
[ "$(id -u)" -eq 0 ] && {
	printf "This script should not be run as root\n" | error
	exit 1
}

ERROR=false

# shellcheck disable=SC2310
command -v uv >/dev/null 2>&1 || {
	printf '%s is not installed, please install it according to your distro\n' uv | error
	ERROR=true
}

# check for wine
command -v wine >/dev/null 2>&1 ||
	printf '%s\n' 'Wine is required to run studiomdl.exe for model precaching' | warning

! ${ERROR} || exit 1 # exit if errors were previously raised

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
exec uv run python ./main.py "${@}"
