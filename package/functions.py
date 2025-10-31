from io import BufferedReader, BufferedWriter
from os import fstat


def read_file(file_path: str) -> tuple[tuple[int, str]]:
    data: tuple[tuple[int, str]] = tuple()

    with open(file_path, 'rb') as file:
        num_entries = read_int(file, 12)
        start_offset = read_int(file, 20)

        for i in range(num_entries):
            entry_offset = 28 + i * 12
            start_index = read_int(file, entry_offset)
            start_id = read_int(file, entry_offset + 4)
            end_id = read_int(file, entry_offset + 8)

            for id in range(start_id, end_id + 1):
                text_offset = read_int(
                    file,
                    start_offset + (start_index + id - start_id) * 4
                )
                text = str()

                if text_offset > 0:
                    text = read_str(file, text_offset)

                data += (id, text),

    return data


def read_int(file: BufferedReader, offset: int) -> int:
    file.seek(offset)
    byte_int = file.read(4)

    return int.from_bytes(byte_int, byteorder='little')


def read_str(file: BufferedReader, offset: int) -> str:
    text = str()
    file.seek(offset)
    fragment = str()

    while chr(0) not in fragment:
        text += fragment
        byte_string = file.read(200)
        fragment = byte_string.decode('utf-16-le')

    end = fragment.find(chr(0))
    text += fragment[:end]
    text = text.replace('\n', '/n/')

    return text


def write_data_to_file(data: tuple[tuple[int, str]], file_path: str) -> None:
    with open(file_path, 'wb') as file:
        entries_amount = chunks_amount = 0
        previous_id = -2

        for item in data:
            if item[0] > previous_id + 1:
                chunks_amount += 1

            entries_amount += 1
            previous_id = item[0]

        start_offset = 28 + chunks_amount * 12
        text_offset = start_offset + entries_amount * 4

        first_id = last_id = data[0][0]
        start_entry = entries_amount = chunks_amount = 0

        for item in data:
            current_id = item[0]

            if current_id > last_id + 1:
                entry_offset = 28 + chunks_amount * 12
                write_int(file=file, int_type=32,
                          offset=entry_offset, value=start_entry)
                write_int(file=file, int_type=32,
                          offset=entry_offset + 4, value=first_id)
                write_int(file=file, int_type=32,
                          offset=entry_offset + 8, value=last_id)

                first_id = current_id
                start_entry = entries_amount
                chunks_amount += 1

            if text := item[1]:
                write_int(
                    file=file,
                    int_type=32,
                    offset=start_offset + entries_amount * 4,
                    value=text_offset
                )

                text = text.replace('/n/', '\n')

                if not text.endswith('\0'):
                    text += '\0'

                write_string(file, text_offset, text)
                text_offset += len(text) * 2

            entries_amount += 1
            last_id = current_id

        file_size = fstat(file.fileno()).st_size
        if file_size % 4 == 2:
            write_int(file=file, int_type=16, offset=text_offset, value=0)

        entry_offset = 28 + chunks_amount * 12
        write_int(file=file, int_type=32,
                  offset=entry_offset, value=start_entry)
        write_int(file=file, int_type=32,
                  offset=entry_offset + 4, value=first_id)
        write_int(file=file, int_type=32,
                  offset=entry_offset + 8, value=last_id)

        write_int(file=file, int_type=32, offset=0, value=65536)
        write_int(file=file, int_type=8, offset=8, value=1)

        write_int(file=file, int_type=32, offset=4, value=file_size)
        write_int(file=file, int_type=32, offset=12, value=chunks_amount + 1)
        write_int(file=file, int_type=32, offset=16, value=entries_amount)
        write_int(file=file, int_type=32, offset=20, value=start_offset)


def write_int(file: BufferedWriter, int_type: int, offset: int, value: int) -> None:
    file.seek(offset)

    match int_type:
        case 8:
            length = 1
        case 16:
            length = 2
        case 32:
            length = 4

    number = value.to_bytes(length, byteorder='little')
    file.write(number)


def write_string(file: BufferedWriter, offset: int, string: str) -> None:
    file.seek(offset)
    encoded_string = string.encode('utf-16-le')
    file.write(encoded_string)
