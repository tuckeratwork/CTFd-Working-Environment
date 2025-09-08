## Author
Developer and Documentation Author:
SPC Casey O'Reilly
casey.e.oreilly.mil@usa.army.mil

Secondary POC: 
SFC Joshua Kollar

## Intentions

The intention of this project is to provide students the ability to reset their PE's while retaining the data of their progress

This will free up instructors from having to constantly reset student pe's and allow students to work on PE's on the weekend when they do not have access to their instructors to reset their PE's for them.

## Methodology

The program provides a page that will be added to the navigation bar if it doens't exist already.

From here students will be prompted to confirm if they want to reset their PE's

If selected, the program will query all their submissions and delete them so long as they're not unlock challenges.

While they're being deleted, the program will also give an Award to the student equivalent to the amount of points their challenges were worth.

In the award description, there will be a breakdown of all the categories of the challenges they solved and their aggregate scores.

The Award category will be named PE Resets

## Instructor Considerations

In order for the unlock challenges not to be deleted, the Unlock challenges must be in the '.Unlock' category

## Usage

To add this plugin to a ctfd instance, the instance must first be taken offline, then the plugin may be added to the plugins folder, and the server restarted. Once restarted the page should be added.

## Known Bugs

Not so much of a bug because it has nothing to do with the program, but due to browser cacheing, the PE Reset page on the navbar probably won't immediately show up.

In addition, after the PE's are reset, the question bubbles may still be highlighted green as if they have been compeleted even though the submissions have been reset.

In order to assuage both of these issues, use Control + Shift + R in your web browser to hard refresh the cached page, and all should be fine.

## Dependencies

This program only uses the built in CTFd dependencies, so no additional installation should be required.

## Future Improvements

If instructors decide to limit the amount of PE resets students are afforded, it is a simple proccess.

The code is already in place to add this feature, but it isn't active. There is a comment where to add the conditional on line 48 of init.py

The code would look like this:

```
check_resets = Awards.query.filter(Awards.user_id == user.id, Awards.category == 'PE Reset').count()

    if check_resets > [number of PE resets allowed]:
        render_template( [error message HTML page] )
    else:
        [normal execution]

```

