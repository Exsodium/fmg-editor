from io import BufferedReader, BufferedWriter
import struct
from os import fstat


def read_file(file_path: str) -> dict[str, str]:
    data = {}

    with open(file_path, 'rb') as file:
        read_int(file, int_type=8, offset=9)

        num_entries = read_int(file, int_type=32, offset=0xC)
        start_offset = read_int(file, int_type=32, offset=0x14)

        for i in range(num_entries):
            entry_offset = 0x1C + i * 0xC
            start_index = read_int(file, int_type=32, offset=entry_offset)
            start_id = read_int(file, int_type=32, offset=entry_offset + 4)
            end_id = read_int(file, int_type=32, offset=entry_offset + 8)

            for id in range(start_id, end_id + 1):
                text_offset = read_int(
                    file,
                    int_type=32,
                    offset=start_offset + (start_index + id - start_id) * 4
                )
                text = str()

                if text_offset > 0:
                    text = read_unicode_string(file, text_offset)
                    text = text.replace('\n', '/n/')

                data[str(id)] = text

    return data


def read_int(file: BufferedReader, int_type: int, offset: int) -> int:
    file.seek(offset)

    match int_type:
        case 8:
            size = 1
            format_char = 'b'
        case 32:
            size = 4
            format_char = 'i'

    data = file.read(size)
    return struct.unpack(f'<{format_char}', data)[0]


def read_unicode_string(file: BufferedReader, offset: int) -> str:
    file.seek(offset)

    data = file.read(1024)

    for i in range(0, len(data) - 1, 2):
        if data[i] == 0 and data[i + 1] == 0:
            data = data[:i]
            break

    return data.decode('utf-16-le') if data else ''


def write_data_to_file(data: dict[str, str], file_path: str) -> None:
    with open(file_path, 'wb') as file:
        entries_amount = 0
        previous_id = -2
        chunks_amount = 0

        for id in data.keys():
            current_id = int(id)

            if current_id > previous_id + 1:
                chunks_amount += 1

            entries_amount += 1
            previous_id = current_id

        start_offset = 0x1c + 0xC * chunks_amount
        text_offset = start_offset + entries_amount * 4

        first_id = int(list(data.keys())[0])
        last_id = first_id
        start_entry = 0
        entries_amount = 0
        chunks_amount = 0

        for id, text in data.items():
            current_id = int(id)

            if current_id > last_id + 1:
                entry_offset = 0x1C + chunks_amount * 0xC
                write_int(file=file, int_type=32,
                          offset=entry_offset, value=start_entry)
                write_int(file=file, int_type=32,
                          offset=entry_offset + 4, value=first_id)
                write_int(file=file, int_type=32,
                          offset=entry_offset + 8, value=last_id)

                first_id = current_id
                start_entry = entries_amount
                chunks_amount += 1

            string = text.replace('\r\n', '')

            if string:
                write_int(
                    file=file,
                    int_type=32,
                    offset=start_offset + entries_amount * 4,
                    value=text_offset
                )

                string = string.replace('/n/', '\n')

                if not string.endswith('\0'):
                    string += '\0'

                write_unicode_string(file, text_offset, string)
                text_offset += len(string) * 2

            entries_amount += 1
            last_id = current_id

        st_size = fstat(file.fileno()).st_size
        if st_size % 4 == 2:
            write_int(file=file, int_type=16, offset=text_offset, value=0)

        write_int(file=file, int_type=32,
                  offset=entry_offset, value=start_entry)
        write_int(file=file, int_type=32,
                  offset=entry_offset + 4, value=first_id)
        write_int(file=file, int_type=32,
                  offset=entry_offset + 8, value=last_id)

        write_int(file=file, int_type=32, offset=0, value=0x10000)
        write_int(file=file, int_type=8, offset=0x8, value=1)

        write_int(file=file, int_type=32, offset=0x4, value=st_size)
        write_int(file=file, int_type=32, offset=0xC, value=chunks_amount + 1)
        write_int(file=file, int_type=32, offset=0x10, value=entries_amount)
        write_int(file=file, int_type=32, offset=0x14, value=start_offset)


def write_int(file: BufferedWriter, int_type: int, offset: int, value: int) -> None:
    file.seek(offset)

    match int_type:
        case 8:
            format = 'b'
        case 16:
            format = '<h'
        case 32:
            format = '<i'

    file.write(struct.pack(format, value))


def write_unicode_string(file: BufferedWriter, offset: int, string: str) -> None:
    file.seek(offset)
    encoded_string = string.encode('utf-16-le')
    file.write(encoded_string)
