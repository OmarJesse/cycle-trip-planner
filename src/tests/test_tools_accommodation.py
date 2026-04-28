from src.tools.find_accommodation import FindAccommodationInput, find_accommodation


def test_find_accommodation_filters():
    out_any = find_accommodation(FindAccommodationInput(near="Hamburg", kind="any"))
    assert len(out_any.options) >= 1

    out_hostel = find_accommodation(FindAccommodationInput(near="Hamburg", kind="hostel"))
    assert all(o.kind == "hostel" for o in out_hostel.options)

