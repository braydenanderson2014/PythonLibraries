# Build: 08/4/2025 [LATEST] # 
* Program: [PDF_Utility]
* Status: [ALPHA]

## Features Added ##
* New Splash Screen! 
* Build system will inject the correct splash screen close functions automatically..
* New Tutorial System
* New Help Documentation

## Improvements Made: ##
* Tutorial System that points out certain useful information and where to find things.
* Help documentation helps you find where things are located.



# Build: 07/28/2025 #
* Program: [PDF_Utility]
* Status: [ALPHA]

## Issues Resolved: ##
* TTS Engine: 
    * Fixed audio broadcasting error: "could not broadcast input array from shape (624,) into shape (624,1)"
    * Fixed thread join error: "cannot join current thread" during cleanup
    * Fixed voice selection ignoring settings - now properly uses Windows SAPI voices (David, Zira, etc.) when selected
    * Added proper audio format handling for both mono and stereo audio streams
    * Improved thread safety and cleanup procedures
    * Fixed voice settings not persisting between application restarts - Settings would always revert to "System Default" after program restart
    * Fixed settings controller singleton pattern to ensure all components use the same settings instance


## Features Added: ##
* TTS Engine: Added support for Windows SAPI voices (David, Zira) in addition to Google TTS
* TTS Settings: Voice selection now populates with actual system voices instead of placeholders
* TTS Widget: Smart navigation buttons that enable/disable based on available pages (Previous/Next Page buttons)

## Improvements Made: ##
* Added the ability to search by "contains" for filenames and for file content
* TTS Engine: Automatic fallback to Google TTS if Windows SAPI fails
* TTS Engine: Improved audio callback with proper shape handling for different audio formats
* TTS Settings: Better voice names displayed (e.g., "David" instead of "Microsoft David Desktop - English (United States)")
* TTS Engine: Settings are now reloaded before each playback to ensure voice changes take effect immediately
* TTS Widget: Navigation buttons now show helpful tooltips with current page information (e.g., "Go to previous page (2/5)")
* TTS Widget: Enhanced user experience with context-aware button states and improved accessibility
* Settings Controller: Implemented singleton pattern to ensure consistent settings across all application components
* TTS Voice Settings: Enhanced voice ID matching for more reliable voice selection and persistence


# Build: 07/27/2025 [Previous] #
* Program: [PDF_Utility]
* Status: [ALPHA]

## Issues Resolved: ##
* Fixed an issue where merge would fail to start
* Fixed an issue where split controller and merge controller would ignore the settings dictated by the settings menu

## Features Added: ##
* Added new Logging settings to the settings menu which will allow you to control where the logs get stored, and how often they get "reset"
* Added a new Icon for the program. Icon present on task bar of os, top left corner of program, and on executable.

## Improvements Made: ##
* Hyper optimized merge controller so it will try to use as little memory as it can manage.
 
    