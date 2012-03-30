<?php
#
# Copyright (c) 2006-2008 Joerg Linge (http://www.pnp4nagios.org)
# Plugin: check_load
# $Id: check_load.php 367 2008-01-23 18:10:31Z pitchfork $
#
#
$opt[1] = "--vertical-label Load -l0  --title \"CPU Load for $hostname / $servicedesc\" ";
#
#
#
$def[1] =  "DEF:var1=$rrdfile:$DS[1]:AVERAGE " ;
$def[1] .= "DEF:var2=$rrdfile:$DS[2]:AVERAGE " ;
$def[1] .= "DEF:var3=$rrdfile:$DS[3]:AVERAGE " ;
$def[1] .= "DEF:var4=$rrdfile:$DS[4]:AVERAGE " ;
$def[1] .= "LINE1:var1#FF0000:\"Total\" " ;
$def[1] .= "GPRINT:var1:LAST:\"%.0lf last\" " ;
$def[1] .= "GPRINT:var1:AVERAGE:\"%.0lf avg\" " ;
$def[1] .= "GPRINT:var1:MAX:\"%.0lf max\\n\" " ;
$def[1] .= "LINE1:var2#0FF000:\"TCP\" " ;
$def[1] .= "GPRINT:var2:LAST:\"%.0lf last\" " ;
$def[1] .= "GPRINT:var2:AVERAGE:\"%.0lf avg\" " ;
$def[1] .= "GPRINT:var2:MAX:\"%.0lf max\\n\" " ;
$def[1] .= "LINE1:var3#000FF0:\"UDP\" " ;
$def[1] .= "GPRINT:var3:LAST:\"%.0lf last\" " ;
$def[1] .= "GPRINT:var3:AVERAGE:\"%.0lf avg\" " ;
$def[1] .= "GPRINT:var3:MAX:\"%.0lf max\\n\" " ;
$def[1] .= "LINE1:var4#00FFFF:\"UNIX\" " ;
$def[1] .= "GPRINT:var4:LAST:\"%.0lf last\" " ;
$def[1] .= "GPRINT:var4:AVERAGE:\"%.0lf avg\" " ;
$def[1] .= "GPRINT:var4:MAX:\"%.0lf max\\n\" " ;
?>
