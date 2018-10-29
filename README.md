## mvnpy

Library that enables abstraction over interaction with Maven framework Java projects


### REQUIREMENTS

* Git (1.7.x or newer)
* Python 2.7

### INSTALL

If you have downloaded the source code:

    python setup.py install


### RUNNING TESTS

To run the the tests, simply run:

    python Test.py


### API

# Initiating repo:

    >>> from Repo import Repo
    >>> mvn_repo = Repo('C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj')

# Applying maven commands:

## test

    C:\Users\user\Code\Python\mvnpy\mvnpy>python2
    Python 2.7.15 |Anaconda, Inc.| (default, May  1 2018, 18:37:09) [MSC v.1500 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from Repo import Repo
    >>> mvn_repo = Repo('C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj')
    >>> build_log = mvn_repo.test()
    [INFO] Scanning for projects...
    [INFO] ------------------------------------------------------------------------
    [INFO] Reactor Build Order:
    [INFO]
    [INFO] GMT_P                                                              [pom]
    [INFO] sub_mod_1                                                          [jar]
    [INFO] sub_mod_2                                                          [jar]
    [INFO]
    [INFO] ----------------------------< GMT_P:GMT_P >-----------------------------
    [INFO] Building GMT_P 1.0-SNAPSHOT                                        [1/3]
    [INFO] --------------------------------[ pom ]---------------------------------
    [INFO]
    [INFO] --------------------------< GMT_P:sub_mod_1 >---------------------------
    [INFO] Building sub_mod_1 1.0-SNAPSHOT                                    [2/3]
    [INFO] --------------------------------[ jar ]---------------------------------
    [INFO]
    [INFO] --- maven-resources-plugin:2.6:resources (default-resources) @ sub_mod_1 ---
    [INFO] Using 'UTF-8' encoding to copy filtered resources.
    [INFO] skip non existing resourceDirectory C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_1\src\main\resources
    [INFO]
    [INFO] --- maven-compiler-plugin:3.1:compile (default-compile) @ sub_mod_1 ---
    [INFO] Nothing to compile - all classes are up to date
    [INFO]
    [INFO] --- maven-resources-plugin:2.6:testResources (default-testResources) @ sub_mod_1 ---
    [INFO] Using 'UTF-8' encoding to copy filtered resources.
    [INFO] skip non existing resourceDirectory C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_1\src\test\resources
    [INFO]
    [INFO] --- maven-compiler-plugin:3.1:testCompile (default-testCompile) @ sub_mod_1 ---
    [INFO] Nothing to compile - all classes are up to date
    [INFO]
    [INFO] --- maven-surefire-plugin:2.22.0:test (default-test) @ sub_mod_1 ---
    [INFO]
    [INFO] -------------------------------------------------------
    [INFO]  T E S T S
    [INFO] -------------------------------------------------------
    [INFO] Running MainTest
    [INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.239 s - in MainTest
    [INFO] Running p_1.AmitTest
    [INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.002 s - in p_1.AmitTest
    [INFO]
    [INFO] Results:
    [INFO]
    [INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
    [INFO]
    [INFO]
    [INFO] --------------------------< GMT_P:sub_mod_2 >---------------------------
    [INFO] Building sub_mod_2 1.0-SNAPSHOT                                    [3/3]
    [INFO] --------------------------------[ jar ]---------------------------------
    [INFO]
    [INFO] --- maven-resources-plugin:2.6:resources (default-resources) @ sub_mod_2 ---
    [INFO] Using 'UTF-8' encoding to copy filtered resources.
    [INFO] skip non existing resourceDirectory C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_2\src\main\resources
    [INFO]
    [INFO] --- maven-compiler-plugin:3.1:compile (default-compile) @ sub_mod_2 ---
    [INFO] Nothing to compile - all classes are up to date
    [INFO]
    [INFO] --- maven-resources-plugin:2.6:testResources (default-testResources) @ sub_mod_2 ---
    [INFO] Using 'UTF-8' encoding to copy filtered resources.
    [INFO] skip non existing resourceDirectory C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_2\src\test\resources
    [INFO]
    [INFO] --- maven-compiler-plugin:3.1:testCompile (default-testCompile) @ sub_mod_2 ---
    [INFO] Nothing to compile - all classes are up to date
    [INFO]
    [INFO] --- maven-surefire-plugin:2.22.0:test (default-test) @ sub_mod_2 ---
    [INFO]
    [INFO] -------------------------------------------------------
    [INFO]  T E S T S
    [INFO] -------------------------------------------------------
    [INFO] Running NaimTest
    [INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.223 s - in NaimTest
    [INFO] Running p_1.AssafTest
    [INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.059 s - in p_1.AssafTest
    [INFO]
    [INFO] Results:
    [INFO]
    [INFO] Tests run: 7, Failures: 0, Errors: 0, Skipped: 0
    [INFO]
    [INFO] ------------------------------------------------------------------------
    [INFO] Reactor Summary:
    [INFO]
    [INFO] GMT_P 1.0-SNAPSHOT ................................. SUCCESS [  0.021 s]
    [INFO] sub_mod_1 .......................................... SUCCESS [ 19.385 s]
    [INFO] sub_mod_2 1.0-SNAPSHOT ............................. SUCCESS [  9.234 s]
    [INFO] ------------------------------------------------------------------------
    [INFO] BUILD SUCCESS
    [INFO] ------------------------------------------------------------------------
    [INFO] Total time: 29.541 s
    [INFO] Finished at: 2018-10-13T14:18:37+03:00
    [INFO] ------------------------------------------------------------------------
## clean

    C:\Users\user\Code\Python\mvnpy\mvnpy>python2
    Python 2.7.15 |Anaconda, Inc.| (default, May  1 2018, 18:37:09) [MSC v.1500 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from Repo import Repo
    >>> mvn_repo = Repo('C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj')
    >>> build_log = mvn_repo.clean()
    [INFO] Scanning for projects...
    [INFO] ------------------------------------------------------------------------
    [INFO] Reactor Build Order:
    [INFO]
    [INFO] GMT_P                                                              [pom]
    [INFO] sub_mod_1                                                          [jar]
    [INFO] sub_mod_2                                                          [jar]
    [INFO]
    [INFO] ----------------------------< GMT_P:GMT_P >-----------------------------
    [INFO] Building GMT_P 1.0-SNAPSHOT                                        [1/3]
    [INFO] --------------------------------[ pom ]---------------------------------
    [INFO]
    [INFO] --- maven-clean-plugin:2.5:clean (default-clean) @ GMT_P ---
    [INFO]
    [INFO] --------------------------< GMT_P:sub_mod_1 >---------------------------
    [INFO] Building sub_mod_1 1.0-SNAPSHOT                                    [2/3]
    [INFO] --------------------------------[ jar ]---------------------------------
    [INFO]
    [INFO] --- maven-clean-plugin:2.5:clean (default-clean) @ sub_mod_1 ---
    [INFO] Deleting C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_1\target
    [INFO]
    [INFO] --------------------------< GMT_P:sub_mod_2 >---------------------------
    [INFO] Building sub_mod_2 1.0-SNAPSHOT                                    [3/3]
    [INFO] --------------------------------[ jar ]---------------------------------
    [INFO]
    [INFO] --- maven-clean-plugin:2.5:clean (default-clean) @ sub_mod_2 ---
    [INFO] Deleting C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_2\target
    [INFO] ------------------------------------------------------------------------
    [INFO] Reactor Summary:
    [INFO]
    [INFO] GMT_P 1.0-SNAPSHOT ................................. SUCCESS [  1.094 s]
    [INFO] sub_mod_1 .......................................... SUCCESS [  0.074 s]
    [INFO] sub_mod_2 1.0-SNAPSHOT ............................. SUCCESS [  0.114 s]
    [INFO] ------------------------------------------------------------------------
    [INFO] BUILD SUCCESS
    [INFO] ------------------------------------------------------------------------
    [INFO] Total time: 1.964 s
    [INFO] Finished at: 2018-10-13T14:21:52+03:00
    [INFO] ------------------------------------------------------------------------
  ## test-compile: mvn_repo.test_compile() ...
  
  If one desires in inspecting a specific submodule (which can decrease the build time significantly), one can specify the module he's interested in:
  
    >>> build_log = mvn_repo.test('MavenProj\sub_mod_1')
    [INFO] Scanning for projects...
    [INFO] ------------------------------------------------------------------------
    [INFO] Reactor Build Order:
    [INFO]
    [INFO] GMT_P                                                              [pom]
    [INFO] sub_mod_1                                                          [jar]
    [INFO]
    [INFO] ----------------------------< GMT_P:GMT_P >-----------------------------
    [INFO] Building GMT_P 1.0-SNAPSHOT                                        [1/2]
    [INFO] --------------------------------[ pom ]---------------------------------
    [INFO]
    [INFO] --------------------------< GMT_P:sub_mod_1 >---------------------------
    [INFO] Building sub_mod_1 1.0-SNAPSHOT                                    [2/2]
    [INFO] --------------------------------[ jar ]---------------------------------
    [INFO]
    [INFO] --- maven-resources-plugin:2.6:resources (default-resources) @ sub_mod_1 ---
    [INFO] Using 'UTF-8' encoding to copy filtered resources.
    [INFO] skip non existing resourceDirectory C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_1\src\main\resources
    [INFO]
    [INFO] --- maven-compiler-plugin:3.1:compile (default-compile) @ sub_mod_1 ---
    [INFO] Changes detected - recompiling the module!
    [INFO] Compiling 2 source files to C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_1\target\classes
    [INFO]
    [INFO] --- maven-resources-plugin:2.6:testResources (default-testResources) @ sub_mod_1 ---
    [INFO] Using 'UTF-8' encoding to copy filtered resources.
    [INFO] skip non existing resourceDirectory C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_1\src\test\resources
    [INFO]
    [INFO] --- maven-compiler-plugin:3.1:testCompile (default-testCompile) @ sub_mod_1 ---
    [INFO] Changes detected - recompiling the module!
    [INFO] Compiling 2 source files to C:\Users\user\Code\Python\mvnpy\mvnpy\examples\MavenProj\sub_mod_1\target\test-classes
    [INFO]
    [INFO] --- maven-surefire-plugin:2.22.0:test (default-test) @ sub_mod_1 ---
    [INFO]
    [INFO] -------------------------------------------------------
    [INFO]  T E S T S
    [INFO] -------------------------------------------------------
    [INFO] Running MainTest
    [INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.063 s - in MainTest
    [INFO] Running p_1.AmitTest
    [INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.002 s - in p_1.AmitTest
    [INFO]
    [INFO] Results:
    [INFO]
    [INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
    [INFO]
    [INFO] ------------------------------------------------------------------------
    [INFO] Reactor Summary:
    [INFO]
    [INFO] GMT_P 1.0-SNAPSHOT ................................. SUCCESS [  0.024 s]
    [INFO] sub_mod_1 1.0-SNAPSHOT ............................. SUCCESS [ 18.848 s]
    [INFO] ------------------------------------------------------------------------
    [INFO] BUILD SUCCESS
    [INFO] ------------------------------------------------------------------------
    [INFO] Total time: 19.454 s
    [INFO] Finished at: 2018-10-13T14:27:12+03:00
    [INFO] ------------------------------------------------------------------------   
  
  # Change pom tags:
  
  ## set_pom_tag(xquery, value , module = '', create_if_not_exist = False)
  
  @module - the path to the module associated with the pom that will be modified
  @xquery - xquey AKA xpath string that describes the tag, that it's text will be change to value
  @create_if_not_exist - setting to true will add tags missing in the pom if they're missing
  
  Example:
  
  BEFORE    
  tika/pom.xml :
 
  .
  .
  .
          
    <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
      <build>
            <plugins>
              <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <configuration>
                  <excludes>
                    <exclude>**/ForkParser*Test.java</exclude>
                  </excludes>
                </configuration>
              </plugin>
            </plugins>
          </build>
    <project>
  .
  .
  .
  
  
    Python 2.7.15 |Anaconda, Inc.| (default, May  1 2018, 18:37:09) [MSC v.1500 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import Repo
    >>> xquery = r"./build/plugins/plugin[artifactId = 'maven-surefire-plugin']/version"
    >>> value = '2.21.0'
    >>> repo = Repo.Repo(r'C:\Users\TEMP\mvnpy\mvnpy\static_files\tika')
    >>> repo.set_pom_tag(xquery = xquery, value = value ,create_if_not_exist=True)


 AFTER    
 tika/pom.xml :


  .
  .
  .
          
    <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.rat</groupId>
                <artifactId>apache-rat-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>CHANGES.txt</exclude>
                    </excludes>
                </configuration>
            </plugin>
            <plugin>
                <artifactId>'maven-surefire-plugin'</artifactId>
                <version>2.21.0</version>
            </plugin>
        </plugins>
    </build>
    <project>
  .
  .
  .
