import io
import logging
import zipfile

log = logging.getLogger(__name__)


def zip_files(files, name=None):
    if not isinstance(files, list):
        files = [files]

    zip_buffer = io.BytesIO()

    if name is None:
        if len(files) == 1:
            zip_name = ".".join(files[0][0].split(".")[0:-1]) + ".zip"
        else:
            zip_name = "report.zip"

    exisiting_size = 0

    with zipfile.ZipFile(
        zip_buffer, "w", zipfile.ZIP_DEFLATED, allowZip64=True
    ) as zip_file:
        for filename, data, content_type in files:
            if hasattr(data, "read"):
                data = data.getvalue()  # or data.read()
            exisiting_size += len(data)
            zip_file.writestr(filename, data)

    print(len(zip_buffer.getvalue()))

    log.info(
        f"Ziping: from {len(files)} files with a total size of {exisiting_size} to {len(zip_buffer.getvalue())} bytes"
    )

    zip_buffer.seek(0)
    return (zip_name, zip_buffer, "application/zip")
