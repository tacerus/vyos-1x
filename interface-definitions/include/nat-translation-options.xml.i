<!-- include start from nat-translation-options.xml.i -->
<node name="options">
  <properties>
    <help>Translation options</help>
  </properties>
  <children>
    <leafNode name="address-mapping">
      <properties>
        <help>Address mapping options</help>
        <completionHelp>
          <list>persistent random</list>
        </completionHelp>
        <valueHelp>
          <format>persistent</format>
          <description>Gives a client the same source or destination-address for each connection</description>
        </valueHelp>
        <valueHelp>
          <format>random</format>
          <description>Random source or destination address allocation for each connection (default)</description>
        </valueHelp>
        <constraint>
          <regex>^(persistent|random)$</regex>
        </constraint>
      </properties>
    </leafNode> 
    <leafNode name="port-mapping">
      <properties>
        <help>Port mapping options</help>
        <completionHelp>
          <list>random fully-random none</list>
        </completionHelp>
        <valueHelp>
          <format>random</format>
          <description>Randomize source port mapping</description>
        </valueHelp>
        <valueHelp>
          <format>fully-random</format>
          <description>Full port randomization</description>
        </valueHelp>
        <valueHelp>
          <format>none</format>
          <description>Do not apply port randomization (default)</description>
        </valueHelp>
        <constraint>
          <regex>^(random|fully-random|none)$</regex>
        </constraint>
      </properties>
    </leafNode> 
  </children>
</node>
<!-- include end -->
