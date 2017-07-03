import cast_upgrade_1_5_9 # @UnusedImport
from cast.application import ApplicationLevelExtension, open_source_file, Bookmark #@UnresolvedImport
import logging


def is_begin(line):
    """
    Return true if the line is the beginning of a user code section
    """
    return '*TELON-' in line

def is_end(line):
    """
    Return true if the line is the end of a user code section
    """
    return '--! END' in line


def get_properties(application):
    """
    Gives all Cobol properties corresponding to bookmarked quality rules
    
    @todo : should probably depend on CAIP version by using : application.get_caip_version()
    """

    properties = [138954, 138955, 138953, 138951, 138910, 138901,
                  138899, 138906, 138911, 138947, 139222, 138904, 138909,
                  138948, 138959, 138902, 139323, 139322, 138900,
                  139020, 138950, 139139, 138589, 139122, 139335,
                  139166, 138949, 138991, 139045, 139321, 139320,
                  138994, 138997, 138907, 139258, 138903, 138594,
                  138995, 139171, 139369, 138998, 139145,
                  138996, 138908, 139405, 139414, 
                  ]
    
    return properties


class FilterViolations(ApplicationLevelExtension):

    def end_application(self, application):
        
        logging.info("Filtering violations")
        
        # All Cobol properties corresponding to bookmarked quality rules
        properties = get_properties(application)
        
        # 1. register each property as handled by this plugin : we wil rewrite them
        for prop in properties:
            application.declare_property_ownership(prop, 'CAST_COBOL_SavedProgram')
        
        for program in application.objects().has_type('CAST_COBOL_SavedProgram').load_violations(properties):
            
            # 1. get the violations for that program
            
            # a Cobol violation can be in a copybook, we group violations per file
            violations_per_file = {}
            
            for prop in properties:
                
                for violation in program.get_violations(prop):
                    
                    logging.info(str(violation))
                    _file = violation[1].file
                    if _file not in violations_per_file:
                        violations_per_file[_file] = []
                    
                    violations_per_file[_file].append(violation)
            
            # 2. filter the violations  that are in user code
            user_code_violations = []
            
            for _file, violations in violations_per_file.items():
                
                # open the file, get the 'user code bookmarks'
                # those are the 'bookmarks' that represent the user code  
                bookmarks = []
                
                with open_source_file(_file.get_path()) as f:
                    
                    begin_line = 0
                    current_line = 0
                    
                    for line in f:
                        current_line += 1
                        
                        if is_begin(line):
                            # store current portion begin
                            begin_line = current_line
                        elif is_end(line):
                            # add a user code bookmark
                            bookmark = Bookmark(_file, 
                                                begin_line,
                                                1,
                                                current_line, -1)
                            
                            bookmarks.append(bookmark)
                
                # filter the violations that reside in at least one 'user code bookmark'
                for violation in violations:
                    
                    for bookmark in bookmarks:
                        # use of contains operator
                        if bookmark.contains(violation[1]):
                            user_code_violations.append(violation)
                            break
                    if not bookmarks:
                        # case where we do not have any marker : keep all violations : maybe we are not in TELON environment
                        user_code_violations.append(violation)
            
            logging.info('saving violations')
            # 3. save back user_code_violations
            for violation in user_code_violations:
                logging.info(violation)
                # violation 'format' is almost directly usable as parameter   
                program.save_violation(violation[0], violation[1], violation[2])
                
            # et hop !

        logging.info("Done filtering violations")