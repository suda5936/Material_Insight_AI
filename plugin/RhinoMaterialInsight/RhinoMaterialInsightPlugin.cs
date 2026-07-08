using Rhino.PlugIns;

namespace RhinoMaterialInsight;

public sealed class RhinoMaterialInsightPlugin : PlugIn
{
    public RhinoMaterialInsightPlugin()
    {
        Instance = this;
    }

    public static RhinoMaterialInsightPlugin? Instance { get; private set; }

    public override PlugInLoadTime LoadTime => PlugInLoadTime.AtStartup;
}
