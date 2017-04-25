
def get_col(row, col):
    for cell in row:
        if cell.value is not None:
            if cell.coordinate.startswith(col):
                return cell


def lb_2_p(txt, sep="\n\n"):
    if sep in txt:
        return "<p>"+"</p><p>".join([l for l in txt.split(sep) if l != ""]) + "</p>"
    else:
        return txt
