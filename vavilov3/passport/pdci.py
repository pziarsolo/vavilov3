

def _calc_score_for_wild(country, collection_site, longitude, latitude,
                         altitude, collection_date, collection_source,
                         collection_number, collection_institute,
                         collection_description):
    score = 0
    if country:
        score += 80
    if latitude and longitude:
        score += 120
        if collection_site:
            score += 20
    elif collection_site:
        score += 70
    if altitude:
        score += 20
    if collection_date:
        score += 30
    if collection_source:
        score += 30
    if collection_number:
        score += 60
    if collection_institute:
        score += 40
    elif collection_description:
        score += 20
    return score


def _calc_score_for_landrace(country, collection_site, longitude, latitude,
                             altitude, collection_date, collection_source,
                             collection_number, collection_institute,
                             collection_description, ancest, germplasm_name):
    score = 0
    if country:
        score += 80
    if latitude and longitude:
        score += 80
        if collection_site:
            score += 15
    elif collection_site:
        score += 45
    if altitude:
        score += 15
    if collection_date:
        score += 30
    if ancest:
        score += 10
    if collection_source:
        score += 50
    if germplasm_name:
        score += 50
    if collection_number:
        score += 40
    if collection_institute:
        score += 30
    elif collection_description:
        score += 15
    return score


def _calc_score_for_breeding(country, breeder_code, ancest, collection_source,
                             germplasm_name, breeder_institute_description):
    score = 0
    if country:
        score += 40

    if breeder_code:
        score += 110

    if ancest:
        score += 150

    if collection_source:
        score += 20

    if germplasm_name:
        score += 80

    if not breeder_code and breeder_institute_description:
        score += 55

    return score


def _calc_score_for_cultivar(country, breeder_code, ancest, collection_source,
                             germplasm_name, breeder_institute_description):
    score = 0
    if country:
        score += 40

    if breeder_code:
        score += 80

    if ancest:
        score += 100

    if collection_source:
        score += 20

    if germplasm_name:
        score += 160

    if not breeder_code and breeder_institute_description:
        score += 40

    return score


def _calc_score_for_unknown(country, collection_site, longitude, latitude,
                            altitude, collection_date, breeder_code,
                            collection_source, collection_number,
                            collection_institute, collection_description,
                            germplasm_name, ancest, breeder_institute_description):
    score = 0
    if country:
        score += 40
    if latitude and longitude:
        score += 30
        if collection_site:
            score += 10
    elif collection_site:
        score += 20

    if altitude:
        score += 5
    if collection_date:
        score += 10

    if breeder_code:
        score += 10

    if ancest:
        score += 40

    if collection_source:
        score += 25
    if germplasm_name:
        score += 40
    if collection_number:
        score += 20
    if collection_institute:
        score += 20
    elif collection_description:
        score += 10

    if not breeder_code and breeder_institute_description:
        score += 40

    return score


def most_complete_subtaxa(subtaxas):
    subtaxa_name = None
    subtaxa_author = None
    for subtaxa in subtaxas.values():
        subtaxa_name = subtaxa.get('name', None)
        subtaxa_author = subtaxa.get('author', None)
        if subtaxa_name and subtaxa_author:
            return subtaxa_name, subtaxa_author

    return subtaxa_name, subtaxa_author


def calculate_pdci(passport):
    score = 0
    if passport.taxonomy.genus:
        score += 120
        if passport.taxonomy.species:
            score += 80
            if passport.taxonomy.species_author:
                score += 5
            subtaxa_name, subtaxa_author = most_complete_subtaxa(passport.taxonomy.subtaxas)
            if subtaxa_name:
                score += 40
                if subtaxa_author:
                    score += 5
    if passport.crop_name:
        score += 45

    if passport.acquisition_date:
        score += 10

    if passport.bio_status:
        score += 80

    if passport.donor.institute:
        score += 40

    if passport.donor.number and not passport.donor.institute and not passport.donor_institute_description:
        score += 20
    elif passport.donor.number and (passport.donor.institute or passport.donor_institute_description):
        score += 40

    if passport.other_numbers:
        score += 35

    if passport.duplication_site_description:
        score += 30

    if passport.germplasm_storage_type:
        score += 15

    if not passport.donor.institute and passport.donor_institute_description:
        score += 20
    if not passport.save_dup_sites and passport.duplication_site_description:
        score += 15

    if passport.germplasm_url:
        score += 40

    if passport.mls_status:
        score += 15

    # BY BIO_STATUS
    country = passport.location.country,
    collection_site = str(passport.location)
    longitude = passport.location.longitude
    latitude = passport.location.latitude,
    altitude = passport.location.altitude
    collection_date = passport.collection_date,
    collection_source = passport.collection_source,
    collection_number = passport.collection.number,
    collection_institute = passport.collection.institute,
    collection_description = passport.collection_institute_description
    germplasm_name = passport.germplasm_name
    breeder_code = passport.breeder_institute_code
    ancest = passport.ancest
    breeder_institute_description = passport.breeder_institute_description
    bio_status_type = passport.bio_status[0] if passport.bio_status else None
    if not bio_status_type:
        pass
    elif bio_status_type in ('1', '2'):
        score += _calc_score_for_wild(country=country,
                                      collection_site=collection_site,
                                      longitude=longitude, latitude=latitude,
                                      altitude=altitude,
                                      collection_date=collection_date,
                                      collection_source=collection_source,
                                      collection_number=collection_number,
                                      collection_institute=collection_institute,
                                      collection_description=collection_description)
    elif bio_status_type == '3':
        score += _calc_score_for_landrace(country=country,
                                          collection_site=collection_site,
                                          longitude=longitude, latitude=latitude,
                                          altitude=altitude,
                                          collection_date=collection_date,
                                          collection_source=collection_source,
                                          collection_number=collection_number,
                                          collection_institute=collection_institute,
                                          collection_description=collection_description,
                                          germplasm_name=germplasm_name,
                                          ancest=passport.ancest)
    elif bio_status_type == '4':
        score += _calc_score_for_breeding(country=country,
                                          breeder_code=breeder_code,
                                          ancest=ancest,
                                          collection_source=collection_source,
                                          germplasm_name=germplasm_name,
                                          breeder_institute_description=breeder_institute_description)
    elif bio_status_type == '5':
        score += _calc_score_for_cultivar(country=country,
                                          breeder_code=breeder_code,
                                          ancest=ancest,
                                          collection_source=collection_source,
                                          germplasm_name=germplasm_name,
                                          breeder_institute_description=breeder_institute_description)
    else:
        score += _calc_score_for_unknown(country=country,
                                         collection_site=collection_site,
                                         longitude=longitude, latitude=latitude,
                                         altitude=altitude,
                                         collection_date=collection_date,
                                         breeder_code=breeder_code,
                                         collection_source=collection_source,
                                         collection_number=collection_number,
                                         collection_institute=collection_institute,
                                         collection_description=collection_description,
                                         germplasm_name=germplasm_name,
                                         ancest=ancest,
                                         breeder_institute_description=breeder_institute_description)

    score = round(score / 100, 2)
    return score
