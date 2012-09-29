<%!
    from crab import CrabStatus

    statuses = set.union(CrabStatus.VALUES, CrabStatus.INTERNAL_VALUES)
%>
function crabStatusName(status_) {
    switch (status_) {
% for status in statuses:
        case ${status}:
            return '${CrabStatus.get_name(status)}';
% endfor
        default:
            return 'Status ' + status_;
    }
}

function crabStatusIsOK(status_) {
    switch (status_) {
% for status in statuses:
%     if CrabStatus.is_ok(status):
        case ${status}:
%     endif
% endfor
            return true;
        default:
            return false;
    }
}

function crabStatusIsWarning(status_) {
    switch (status_) {
% for status in statuses:
%     if CrabStatus.is_warning(status):
        case ${status}:
%     endif
% endfor
            return true;
        default:
            return false;
    }
}
