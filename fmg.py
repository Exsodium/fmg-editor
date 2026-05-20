from functools import partial
from pathlib import Path


def read_fmg(file_path: Path) -> tuple[tuple[int, str], ...]:
    with open(file_path, mode='rb') as f:
        data = f.read()

    int_from_bytes_le = partial(int.from_bytes, byteorder='little')
    blocks_amount = int_from_bytes_le(data[12:16])
    ids = []

    for i in range(blocks_amount):
        start_id_index = 32 + 12*i
        end_id_index = start_id_index + 4

        start_id = int_from_bytes_le(data[start_id_index : end_id_index])
        end_id = int_from_bytes_le(data[end_id_index : end_id_index + 4])

        ids.extend(range(start_id, end_id + 1))

    lines_amount = int_from_bytes_le(data[16:20])
    text_offsets_offset = int_from_bytes_le(data[20:24])
    text_offsets = []

    for i in range(lines_amount):
        offset_index = text_offsets_offset + 4*i
        offset_value = int_from_bytes_le(data[offset_index : offset_index + 4])

        text_offsets.append(offset_value)

    not_empty_text_offset_index = next(filter(None, text_offsets))
    byte_lines = data[not_empty_text_offset_index:]
    blocks = [byte_lines[i : i + 2] for i in range(0, len(byte_lines), 2)]

    lines = []
    byte_line = b''
    for block in blocks:
        if block == b'\x00\x00':
            line = byte_line.decode('utf-16-le')
            lines.append(line)
            byte_line = b''
            continue

        byte_line += block

    line_iterator = iter(lines)
    content = []

    for id_, offset in zip(ids, text_offsets):
        content.append((id_, next(line_iterator) if offset else ''))

    return tuple(content)


def write_fmg(data: tuple[tuple[int, str], ...], file_path: Path) -> None:
    blocks_amount = 1 + sum(1 for i in range(1, len(data)) if data[i][0] != data[i - 1][0] + 1)
    lines_amount = len(data)
    text_offsets_offset = 28 + 12*blocks_amount

    with open(file_path, 'wb') as file:
        file.write((0x10000000000010000).to_bytes(12, 'little'))
        file.write(blocks_amount.to_bytes(4, 'little'))
        file.write(lines_amount.to_bytes(4, 'little'))
        file.write(text_offsets_offset.to_bytes(4, 'little'))
        file.write(b'\0' * 8)

        first_id = last_id = data[0][0]
        line_index = 0
        meta_offset = file.tell()
        text_offset = text_offsets_offset + 4*lines_amount

        for id_, text in data:
            if id_ > last_id + 1:
                file.seek(meta_offset)
                file.write(first_id.to_bytes(4, 'little'))
                file.write(last_id.to_bytes(4, 'little'))
                file.write(line_index.to_bytes(4, 'little'))

                meta_offset = file.tell()
                first_id = id_

            if text:
                file.seek(text_offsets_offset + 4*line_index)
                file.write(text_offset.to_bytes(4, 'little'))

                file.seek(text_offset)
                text_offset += (len(text) + 1) * 2
                text += '\0'
                file.write(text.encode('utf-16le'))

            last_id = id_
            line_index += 1
        else:
            file.seek(meta_offset)
            file.write(first_id.to_bytes(4, 'little'))
            file.write(last_id.to_bytes(4, 'little'))

        file.seek(0, 2)
        position = file.tell()
        if position % 32 != 0:
            file.write(b'\0' * (32 - position % 32))

        file_size = file.tell()
        file.seek(4)
        file.write(file_size.to_bytes(4, 'little'))
